"""Scholastica student API — the authoritative student database.

Each parent is linked to exactly one student and the server returns ONLY that
student's report. A parent requesting another student's record gets 403, so the
data never reaches an unauthorized browser (unlike the static portal, where all
data ships to every client). Teachers/admins may read any student.

Auth is token-based (stateless, signed with itsdangerous) so the cross-origin
parent app can send `Authorization: Bearer <token>` without cookie/SameSite
headaches. Seed accounts and data cover the two demo students, Maya and James.
"""
import json
import os
import sqlite3

from flask import Flask, request, jsonify, g
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired

app = Flask(__name__)
CORS(app)  # token-based (no cookies) → allowing all origins is safe for this demo

SECRET = os.environ.get("SECRET_KEY", "dev-change-me")
DB_PATH = os.environ.get("DB_PATH", "/data/students.db")
TOKEN_MAX_AGE = 60 * 60 * 12  # 12 hours
signer = URLSafeTimedSerializer(SECRET, salt="scholastica-auth")


# ---------- database ----------
def db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(_exc):
    conn = g.pop("db", None)
    if conn is not None:
        conn.close()


def init_db():
    os.makedirs(os.path.dirname(DB_PATH) or ".", exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS students (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            program TEXT NOT NULL,
            grade TEXT NOT NULL,
            report_json TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL,                 -- admin | teacher | parent | student
            name TEXT NOT NULL,
            student_id TEXT                     -- the child (parent) or self (student)
        );
        """
    )
    if conn.execute("SELECT COUNT(*) FROM students").fetchone()[0] == 0:
        seed(conn)
    conn.commit()
    conn.close()


def seed(conn):
    students = [
        (
            "maya", "Maya Chen", "Grade 5/6 (Primary)", "Grade 6 · Room 6B",
            {
                "grading": "letter",
                "term": "Term 2 · 2025-26",
                "subjects": [
                    {"name": "Mathematics", "code": "Gr6 · Math", "score": 92, "attended": 56, "total": 58, "trend": "up"},
                    {"name": "English Language Arts", "code": "Gr6 · ELA", "score": 88, "attended": 57, "total": 58, "trend": "flat"},
                    {"name": "Science", "code": "Gr6 · Sci", "score": 95, "attended": 55, "total": 58, "trend": "up"},
                    {"name": "Social Studies", "code": "Gr6 · SS", "score": 84, "attended": 54, "total": 58, "trend": "down"},
                    {"name": "Reading", "code": "Gr6 · Read", "score": 90, "attended": 58, "total": 58, "trend": "up"},
                    {"name": "Art", "code": "Gr6 · Art", "score": 97, "attended": 28, "total": 29, "trend": "up"},
                    {"name": "Physical Education", "code": "Gr6 · PE", "score": 93, "attended": 27, "total": 29, "trend": "flat"},
                ],
                "trend": [
                    {"term": "Q1", "value": 85}, {"term": "Q2", "value": 87},
                    {"term": "Q3", "value": 89}, {"term": "Q4", "value": 91},
                ],
                "achievement": {"tag": "Recognition", "title": "Honor Roll",
                                "note": "Maya kept a term average above 90% — she's on the Grade 6 Honor Roll."},
            },
        ),
        (
            "james", "James Carter", "GED", "GED Prep · Evening",
            {
                "grading": "ged",
                "term": "GED Prep · Spring Cohort",
                "subjects": [
                    {"name": "Mathematical Reasoning", "code": "GED · Math", "score": 158, "attended": 22, "total": 24, "trend": "up"},
                    {"name": "Reasoning Through Language Arts", "code": "GED · RLA", "score": 165, "attended": 23, "total": 24, "trend": "up"},
                    {"name": "Science", "code": "GED · Sci", "score": 149, "attended": 21, "total": 24, "trend": "flat"},
                    {"name": "Social Studies", "code": "GED · SS", "score": 152, "attended": 20, "total": 24, "trend": "up"},
                ],
                "trend": [
                    {"term": "Test 1", "value": 138}, {"term": "Test 2", "value": 146},
                    {"term": "Test 3", "value": 152}, {"term": "Test 4", "value": 156},
                ],
                "achievement": {"tag": "Test Readiness", "title": "3 of 4 Passing",
                                "note": "James is passing 3 of the 4 GED subjects — one more (Science) to be test-ready."},
            },
        ),
    ]
    for sid, name, program, grade, report in students:
        conn.execute(
            "INSERT INTO students (id, name, program, grade, report_json) VALUES (?,?,?,?,?)",
            (sid, name, program, grade, json.dumps(report)),
        )

    users = [
        ("admin", "admin123", "admin", "Principal Hale", None),
        ("teacher", "teach123", "teacher", "Ms. Rivera", None),
        ("maya", "maya123", "student", "Maya Chen", "maya"),
        ("james", "james123", "student", "James Carter", "james"),
        ("parent_maya", "parent123", "parent", "R. Chen", "maya"),
        ("parent_james", "parent123", "parent", "D. Carter", "james"),
    ]
    for username, pw, role, name, sid in users:
        conn.execute(
            "INSERT INTO users (username, password_hash, role, name, student_id) VALUES (?,?,?,?,?)",
            (username, generate_password_hash(pw), role, name, sid),
        )


# ---------- auth helpers ----------
def make_token(user_id):
    return signer.dumps({"uid": user_id})


def current_user():
    """Resolve the Bearer token to a user row, or None."""
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        return None
    try:
        data = signer.loads(auth[7:], max_age=TOKEN_MAX_AGE)
    except (BadSignature, SignatureExpired):
        return None
    return db().execute("SELECT * FROM users WHERE id = ?", (data.get("uid"),)).fetchone()


def require_user():
    u = current_user()
    if u is None:
        return None, (jsonify({"error": "Unauthorized"}), 401)
    return u, None


def can_view_student(user, student_id):
    if user["role"] in ("admin", "teacher"):
        return True
    return user["student_id"] == student_id


def student_payload(row, include_report=True):
    out = {"id": row["id"], "name": row["name"], "program": row["program"], "grade": row["grade"]}
    if include_report:
        out["report"] = json.loads(row["report_json"])
    return out


# ---------- routes ----------
@app.get("/api/health")
def health():
    return {"ok": True}


@app.post("/api/login")
def login():
    body = request.get_json(silent=True) or {}
    username = (body.get("username") or "").strip().lower()
    password = body.get("password") or ""
    row = db().execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
    if not row or not check_password_hash(row["password_hash"], password):
        return jsonify({"error": "Incorrect username or password."}), 401
    user = {"username": row["username"], "role": row["role"], "name": row["name"], "student_id": row["student_id"]}
    return jsonify({"token": make_token(row["id"]), "user": user})


@app.get("/api/me")
def me():
    user, err = require_user()
    if err:
        return err
    return jsonify({"username": user["username"], "role": user["role"], "name": user["name"], "student_id": user["student_id"]})


@app.get("/api/students")
def list_students():
    user, err = require_user()
    if err:
        return err
    if user["role"] not in ("admin", "teacher"):
        return jsonify({"error": "Forbidden"}), 403
    rows = db().execute("SELECT * FROM students ORDER BY name").fetchall()
    return jsonify([student_payload(r, include_report=False) for r in rows])


@app.get("/api/students/<sid>")
def get_student(sid):
    user, err = require_user()
    if err:
        return err
    if not can_view_student(user, sid):
        # Parent A asking for student B lands here — data is never returned.
        return jsonify({"error": "Forbidden — you may only view your own student's report."}), 403
    row = db().execute("SELECT * FROM students WHERE id = ?", (sid,)).fetchone()
    if not row:
        return jsonify({"error": "Not found"}), 404
    return jsonify(student_payload(row))


@app.get("/api/my-report")
def my_report():
    """Convenience for parents/students: the caller's own authorized report."""
    user, err = require_user()
    if err:
        return err
    sid = user["student_id"]
    if not sid:
        return jsonify({"error": "This account is not linked to a student."}), 400
    row = db().execute("SELECT * FROM students WHERE id = ?", (sid,)).fetchone()
    if not row:
        return jsonify({"error": "Not found"}), 404
    return jsonify(student_payload(row))


init_db()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
