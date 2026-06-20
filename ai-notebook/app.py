"""Scholastica AI Notebook — "ask my school notes" (RAG) for students.

A teacher uploads notes/PDFs (admin); students ask questions and the answer is
grounded in those notes, not the model's imagination:

  question → embed → top-K similar chunks → inject into prompt → stream answer

Design choices for a modest CPU-only school server:
  - Embeddings: Ollama (EMBED_MODEL, e.g. nomic-embed-text) — local, free.
  - Vector store: a tiny built-in store (SQLite + numpy cosine). For a school's
    notes this is instant and dependency-light; swap in ChromaDB if the corpus
    grows into the millions of chunks.
  - Generation: delegated to the ai-proxy (PROXY_URL), so it inherits the
    local-first + cloud-fallback behaviour and the single-inference queue.

Endpoints:
  GET  /                     chat + admin UI
  GET  /health               status (ollama/proxy reachable, chunk count)
  POST /api/ingest           (admin) upload a .pdf/.txt/.md → chunk+embed+store
  GET  /api/docs             (admin) list ingested docs
  DELETE /api/docs/{id}      (admin) remove a doc and its chunks
  POST /api/chat             {question} → SSE stream grounded in the notes
"""
import io
import os
import re
import sqlite3

import httpx
import numpy as np
from fastapi import FastAPI, Request, UploadFile, File, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse

OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://host.docker.internal:11434").rstrip("/")
EMBED_MODEL = os.environ.get("EMBED_MODEL", "nomic-embed-text")
PROXY_URL = os.environ.get("PROXY_URL", "http://ai-proxy:8000/v1").rstrip("/")
ADMIN_TOKEN = os.environ.get("ADMIN_TOKEN", "change-me-notebook-admin")
TOP_K = int(os.environ.get("TOP_K", "3"))
CHUNK_CHARS = int(os.environ.get("CHUNK_CHARS", "1600"))   # ~400 tokens
CHUNK_OVERLAP = int(os.environ.get("CHUNK_OVERLAP", "200"))
DB_PATH = os.environ.get("DB_PATH", "/data/notebook.db")
HERE = os.path.dirname(__file__)

app = FastAPI(title="Scholastica AI Notebook")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


# ---------- storage ----------
def db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    os.makedirs(os.path.dirname(DB_PATH) or ".", exist_ok=True)
    conn = db()
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS docs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            created TEXT DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS chunks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            doc_id INTEGER NOT NULL REFERENCES docs(id) ON DELETE CASCADE,
            text TEXT NOT NULL,
            embedding BLOB NOT NULL
        );
        """
    )
    conn.commit()
    conn.close()


init_db()


# ---------- helpers ----------
def require_admin(token):
    if token != ADMIN_TOKEN:
        raise HTTPException(status_code=403, detail="Admin token required.")


def chunk_text(text):
    text = re.sub(r"\s+", " ", text or "").strip()
    out, i, step = [], 0, max(1, CHUNK_CHARS - CHUNK_OVERLAP)
    while i < len(text):
        piece = text[i:i + CHUNK_CHARS].strip()
        if piece:
            out.append(piece)
        i += step
    return out


def extract_text(filename, raw):
    name = (filename or "").lower()
    if name.endswith(".pdf"):
        from pypdf import PdfReader
        reader = PdfReader(io.BytesIO(raw))
        return "\n".join((p.extract_text() or "") for p in reader.pages)
    return raw.decode("utf-8", errors="ignore")


async def embed(text):
    async with httpx.AsyncClient(timeout=60) as c:
        r = await c.post(OLLAMA_URL + "/api/embeddings", json={"model": EMBED_MODEL, "prompt": text})
        r.raise_for_status()
        return np.asarray(r.json()["embedding"], dtype=np.float32)


async def retrieve(question, k):
    conn = db()
    rows = conn.execute(
        "SELECT chunks.text AS text, docs.title AS title, chunks.embedding AS emb "
        "FROM chunks JOIN docs ON docs.id = chunks.doc_id"
    ).fetchall()
    conn.close()
    if not rows:
        return []
    mat = np.stack([np.frombuffer(r["emb"], dtype=np.float32) for r in rows])
    q = await embed(question)
    mat_n = mat / (np.linalg.norm(mat, axis=1, keepdims=True) + 1e-9)
    q_n = q / (np.linalg.norm(q) + 1e-9)
    sims = mat_n @ q_n
    top = np.argsort(-sims)[:k]
    return [(rows[i]["text"], rows[i]["title"], float(sims[i])) for i in top]


# ---------- routes ----------
@app.get("/", response_class=HTMLResponse)
async def index():
    with open(os.path.join(HERE, "static", "index.html"), encoding="utf-8") as f:
        return f.read()


@app.get("/health")
async def health():
    conn = db()
    docs = conn.execute("SELECT COUNT(*) FROM docs").fetchone()[0]
    chunks = conn.execute("SELECT COUNT(*) FROM chunks").fetchone()[0]
    conn.close()

    async def up(url):
        try:
            async with httpx.AsyncClient(timeout=3) as c:
                return (await c.get(url)).status_code < 500
        except Exception:
            return False

    return {
        "docs": docs, "chunks": chunks,
        "ollama": {"url": OLLAMA_URL, "up": await up(OLLAMA_URL + "/api/tags")},
        "proxy": {"url": PROXY_URL, "up": await up(PROXY_URL + "/models")},
        "embed_model": EMBED_MODEL,
    }


@app.post("/api/ingest")
async def ingest(file: UploadFile = File(...), x_admin_token: str = Header(default="")):
    require_admin(x_admin_token)
    raw = await file.read()
    try:
        text = extract_text(file.filename, raw)
    except Exception as e:
        raise HTTPException(status_code=400, detail="Could not read file: %s" % e)
    pieces = chunk_text(text)
    if not pieces:
        raise HTTPException(status_code=400, detail="No readable text found in the file.")

    conn = db()
    cur = conn.execute("INSERT INTO docs (title) VALUES (?)", (file.filename,))
    doc_id = cur.lastrowid
    try:
        for piece in pieces:
            vec = await embed(piece)
            conn.execute("INSERT INTO chunks (doc_id, text, embedding) VALUES (?,?,?)",
                         (doc_id, piece, vec.tobytes()))
        conn.commit()
    except Exception as e:
        conn.rollback()
        conn.execute("DELETE FROM docs WHERE id = ?", (doc_id,))
        conn.commit()
        conn.close()
        raise HTTPException(status_code=502, detail="Embedding failed (is Ollama running with '%s'?): %s" % (EMBED_MODEL, e))
    conn.close()
    return {"doc_id": doc_id, "title": file.filename, "chunks": len(pieces)}


@app.get("/api/docs")
async def list_docs(x_admin_token: str = Header(default="")):
    require_admin(x_admin_token)
    conn = db()
    rows = conn.execute(
        "SELECT docs.id, docs.title, docs.created, COUNT(chunks.id) AS chunks "
        "FROM docs LEFT JOIN chunks ON chunks.doc_id = docs.id GROUP BY docs.id ORDER BY docs.id DESC"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


@app.delete("/api/docs/{doc_id}")
async def delete_doc(doc_id: int, x_admin_token: str = Header(default="")):
    require_admin(x_admin_token)
    conn = db()
    conn.execute("DELETE FROM chunks WHERE doc_id = ?", (doc_id,))
    conn.execute("DELETE FROM docs WHERE id = ?", (doc_id,))
    conn.commit()
    conn.close()
    return {"deleted": doc_id}


SYSTEM = (
    "You are a study assistant for school students. Answer the QUESTION using ONLY the school notes in "
    "CONTEXT. If the answer is not in the notes, say you don't know and suggest asking a teacher — do not "
    "make things up. Be clear and concise, and mention the [source] titles you used."
)


@app.post("/api/chat")
async def chat(req: Request):
    body = await req.json()
    question = (body.get("question") or "").strip()
    if not question:
        raise HTTPException(status_code=400, detail="Empty question.")

    try:
        hits = await retrieve(question, TOP_K)
    except Exception as e:
        return JSONResponse({"error": "Retrieval failed (Ollama/embeddings): %s" % e}, status_code=502)

    if not hits:
        def empty():
            msg = "No school notes have been uploaded yet. Ask your teacher to add notes in the admin panel."
            import json
            yield ("data: " + json.dumps({"choices": [{"delta": {"content": msg}}]}) + "\n\n").encode()
            yield b"data: [DONE]\n\n"
        return StreamingResponse(empty(), media_type="text/event-stream")

    context = "\n\n".join("[%s] %s" % (title, text) for text, title, _ in hits)
    messages = [
        {"role": "system", "content": SYSTEM},
        {"role": "user", "content": "CONTEXT:\n%s\n\nQUESTION: %s" % (context, question)},
    ]

    async def gen():
        payload = {"model": "local", "stream": True, "messages": messages, "temperature": 0.2}
        try:
            async with httpx.AsyncClient(timeout=180) as c:
                async with c.stream("POST", PROXY_URL + "/chat/completions", json=payload) as resp:
                    async for chunk in resp.aiter_bytes():
                        if chunk:
                            yield chunk
        except Exception as e:
            import json
            err = {"choices": [{"delta": {"content": "⚠️ Could not reach the model via the AI proxy: %s" % e}}]}
            yield ("data: " + json.dumps(err) + "\n\n").encode()
            yield b"data: [DONE]\n\n"

    return StreamingResponse(gen(), media_type="text/event-stream")
