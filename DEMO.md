# Scholastica — Demo Access

Quick reference for demoing the portal. Start everything with:

```bash
docker compose up -d --build
```

> ⚠️ **Demo credentials only — not real security.** The portal's accounts are checked in the browser;
> the exam app ships a default admin. Change all of these before any real or public deployment.

## URLs

| App | URL | What it is |
|-----|-----|------------|
| 🏫 **Main portal** | http://localhost:8080 | Full app — students & teachers (keep internal) |
| 👪 **Parent portal** | http://localhost:8081 | Per-child report view (needs the Student API on 8085) |
| 📚 **E-Library** | http://localhost:8082 | Launcher for the Calibre library |
| 📝 **Exam app** | http://localhost:8084 | Separate Flask exam system (its own login) |
| 🗄️ **Student API** | http://localhost:8085 | Backend for the parent portal (per-child reports) |

Over a VS Code tunnel, replace `localhost:<port>` with each forwarded `https://…devtunnels.ms` URL.

**Remote admin (setup/maintenance):** on the server run `code tunnel service install`, then open
`https://vscode.dev/tunnel/<machine>` for a browser terminal + editor + port forwarding. Full steps in
the README's *Remote access* section.

## Main portal accounts (8080)

Client-side demo sign-in for the full portal:

| Username | Password | Role | What they can do |
|----------|----------|------|------------------|
| `teacher` | `teach123` | Teacher | Everything + **edit grades** on the Grades page |
| `admin` | `admin123` | Admin | Everything + edit grades |
| `maya` | `maya123` | Student | Read-only — Grade 6 program |
| `james` | `james123` | Student | Read-only — GED program |
| `parent` | `parent123` | Parent | Read-only (static demo view) |

**Demo flow:** sign in as `teacher` on 8080 → **Grades** → **Edit** → change a score → **Save**
(fires a "new grade posted" notification). Then sign in as `maya` to see the read-only student view.

## Parent portal accounts (8081, via Student API)

The parent portal is backed by the **Student API** (8085) and enforces per-child access on the
**server** — a parent can only see their own child's report.

| Username | Password | Sees |
|----------|----------|------|
| `parent_maya` | `parent123` | **only** Maya's report |
| `parent_james` | `parent123` | **only** James's report |

**Demo flow:** open 8081 → sign in as `parent_maya` → you see Maya's report. There is no way to reach
James's data (the server returns 403). Sign out, sign in as `parent_james` to see the other child.

## Research AI assistant (offline, LM Studio)

The Research page (on the portal, 8080) has an **AI Research Assistant** that runs offline on a local
LM Studio model — no account needed.

1. Install **LM Studio** (`winget install ElementLabs.LMStudio`) and download **Gemma 3 4B Instruct**.
2. LM Studio → **Developer** tab → load the model → **Start Server** (port 1234) → **enable CORS**.
3. Research page → **AI Research Assistant** → ⚙️ → server `http://localhost:1234/v1` → **Test** → chat.

Use it over `http://localhost:8080` (offline/local) — not over an HTTPS tunnel (mixed-content block).

## Exam app account (8084)

The exam app has its **own** login, separate from the portal.

| Username | Password | Role |
|----------|----------|------|
| `admin` | `admin` | Admin |

The admin creates teacher/student accounts and exams from the admin dashboard. From the portal's
**Exam Center** page, set the **Exam Server** address to `http://localhost:8084` (or the tunnel URL)
and click **Open Exam App**.

## E-Library (8082 / calibre-web on 8083)

The E-Library is a launcher. You need two things:

1. **Calibre desktop** (`winget install calibre.calibre`) to build a library folder — Add books, which
   creates `metadata.db`.
2. **calibre-web** in Docker on port 8083, pointed at that folder. Default login below.

| Service | URL | Username | Password |
|---------|-----|----------|----------|
| calibre-web | http://localhost:8083 | `admin` | `admin123` (change on first login) |

Then on the E-Library page (8082) set the **Library Server** address to `http://localhost:8083`
(or the tunnel URL). Full steps are in the README's *E-Library (Calibre)* section.
