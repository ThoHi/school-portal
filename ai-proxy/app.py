"""Scholastica AI proxy — one OpenAI-compatible endpoint for the Research chat.

Tries a LOCAL model first (Ollama or LM Studio, both speak the OpenAI API) and
falls back to a CLOUD provider when local is unavailable. The cloud API key is
held here, server-side, so it never reaches the browser.

The cloud adapter is OpenAI-compatible (works with OpenAI, OpenRouter, Together,
Groq, etc. by setting CLOUD_API_URL / CLOUD_API_KEY / CLOUD_MODEL). Anthropic's
native API has a different shape — plug it in later via the CLOUD_FORMAT hook.

Endpoints: GET /health · GET /v1/models · POST /v1/chat/completions (stream).
Env:
  LOCAL_API_URL   default http://host.docker.internal:11434/v1  (Ollama on host)
  LOCAL_MODEL     optional: force this model for local requests
  CLOUD_API_URL   e.g. https://openrouter.ai/api/v1  ("" disables cloud)
  CLOUD_API_KEY   cloud key (kept server-side)
  CLOUD_MODEL     model id to use for cloud requests
  MAX_CONCURRENCY default 1 (CPU does ~1 inference at a time)
"""
import asyncio
import json
import os

import httpx
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse

LOCAL_API_URL = os.environ.get("LOCAL_API_URL", "http://host.docker.internal:11434/v1").rstrip("/")
LOCAL_MODEL = os.environ.get("LOCAL_MODEL", "").strip()
CLOUD_API_URL = os.environ.get("CLOUD_API_URL", "").rstrip("/")
CLOUD_API_KEY = os.environ.get("CLOUD_API_KEY", "").strip()
CLOUD_MODEL = os.environ.get("CLOUD_MODEL", "").strip()
MAX_CONCURRENCY = int(os.environ.get("MAX_CONCURRENCY", "1"))
TIMEOUT = float(os.environ.get("REQUEST_TIMEOUT", "180"))

CLOUD_ENABLED = bool(CLOUD_API_URL and CLOUD_API_KEY)

app = FastAPI(title="Scholastica AI proxy")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# CPU does ~1 inference at a time; this serializes requests (a simple queue).
_sem = asyncio.Semaphore(max(1, MAX_CONCURRENCY))
_busy = 0


async def local_up() -> bool:
    try:
        async with httpx.AsyncClient(timeout=3) as c:
            r = await c.get(LOCAL_API_URL + "/models")
            return r.status_code < 500
    except Exception:
        return False


def _backend(name):
    if name == "local":
        return {"name": "local", "url": LOCAL_API_URL, "key": "", "model": LOCAL_MODEL}
    return {"name": "cloud", "url": CLOUD_API_URL, "key": CLOUD_API_KEY, "model": CLOUD_MODEL}


async def _chain():
    """Backends to try, in order (prefer a reachable local model)."""
    order = []
    if await local_up():
        order.append(_backend("local"))
        if CLOUD_ENABLED:
            order.append(_backend("cloud"))
    else:
        if CLOUD_ENABLED:
            order.append(_backend("cloud"))
        order.append(_backend("local"))  # last-ditch attempt
    return order


@app.get("/health")
async def health():
    return {
        "local": {"url": LOCAL_API_URL, "up": await local_up()},
        "cloud": {"configured": CLOUD_ENABLED, "model": CLOUD_MODEL or None},
        "busy": _busy,
        "max_concurrency": MAX_CONCURRENCY,
    }


@app.get("/v1/models")
async def models():
    if await local_up():
        try:
            async with httpx.AsyncClient(timeout=3) as c:
                r = await c.get(LOCAL_API_URL + "/models")
                return JSONResponse(r.json())
        except Exception:
            pass
    return {"object": "list", "data": [{"id": CLOUD_MODEL or "ai-proxy", "object": "model"}]}


def _prep(body, backend):
    payload = dict(body)
    if backend["model"]:
        payload["model"] = backend["model"]
    headers = {"Content-Type": "application/json"}
    if backend["key"]:
        headers["Authorization"] = "Bearer " + backend["key"]
    return payload, headers


def _sse_error(msg):
    chunk = {"choices": [{"delta": {"content": "⚠️ " + msg}, "finish_reason": "stop"}]}
    return ("data: " + json.dumps(chunk) + "\n\n" + "data: [DONE]\n\n").encode()


async def _stream(chain, body):
    global _busy
    async with _sem:
        _busy += 1
        try:
            last_err = "no backend configured"
            for b in chain:
                payload, headers = _prep(body, b)
                payload["stream"] = True
                try:
                    async with httpx.AsyncClient(timeout=TIMEOUT) as c:
                        async with c.stream("POST", b["url"] + "/chat/completions",
                                            json=payload, headers=headers) as resp:
                            if resp.status_code >= 400:
                                last_err = "%s HTTP %s" % (b["name"], resp.status_code)
                                await resp.aread()
                                continue
                            async for chunk in resp.aiter_bytes():
                                if chunk:
                                    yield chunk
                            return
                except Exception as e:  # connection failed → try next backend
                    last_err = "%s: %s" % (b["name"], e)
                    continue
            yield _sse_error("No LLM backend available (" + last_err + ").")
        finally:
            _busy -= 1


@app.post("/v1/chat/completions")
async def chat(req: Request):
    body = await req.json()
    chain = await _chain()
    if not chain:
        return JSONResponse({"error": "No backend available"}, status_code=503)

    if body.get("stream"):
        return StreamingResponse(_stream(chain, body), media_type="text/event-stream")

    # non-streaming
    global _busy
    async with _sem:
        _busy += 1
        try:
            last_err = "no backend configured"
            for b in chain:
                payload, headers = _prep(body, b)
                payload["stream"] = False
                try:
                    async with httpx.AsyncClient(timeout=TIMEOUT) as c:
                        r = await c.post(b["url"] + "/chat/completions", json=payload, headers=headers)
                        if r.status_code >= 400:
                            last_err = "%s HTTP %s" % (b["name"], r.status_code)
                            continue
                        return JSONResponse(r.json(), headers={"X-LLM-Backend": b["name"]})
                except Exception as e:
                    last_err = "%s: %s" % (b["name"], e)
                    continue
            return JSONResponse({"error": "All backends failed", "detail": last_err}, status_code=502)
        finally:
            _busy -= 1
