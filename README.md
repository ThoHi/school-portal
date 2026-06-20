# Scholastica — Academic Excellence Portal

A unified school management portal for **students, teachers, and parents**, built as an installable
[Progressive Web App (PWA)](https://web.dev/progressive-web-apps/). It works offline and can be added
to a phone or desktop home screen.

> 🚫 **Non-commercial use only.** Free for schools, nonprofits, research, and personal use —
> **not for commercial use**. Licensed under [PolyForm Noncommercial 1.0.0](LICENSE). See
> [License](#license).

## Programs

The school runs two programs, and the portal switches between them with a **track toggle** (top of the
Dashboard, Grades, and Attendance pages). The choice is saved in the browser and shared across pages.

- **Grade 5/6 (Primary)** — elementary subjects (Math, English Language Arts, Science, Social Studies,
  Reading, Art, PE) graded with **letter grades + percentages** (e.g. 92% = A−).
- **GED** — the four GED subjects (Mathematical Reasoning, RLA, Science, Social Studies) scored on the
  official **100–200 scale** (145 = pass, 165 = college-ready, 175 = honors).

Track data and grading helpers live in `app.js`.

## Pages

The full portal lives in `apps/portal/`:

| Page | File | Description |
|------|------|-------------|
| Dashboard | `apps/portal/index.html` | Main landing dashboard and navigation hub |
| Attendance | `apps/portal/attendance.html` | Attendance tracking — rates by course, calendar heatmap, activity log |
| Grades | `apps/portal/grades.html` | Grades & GPA — per-course grades, weighted GPA, trend chart by semester |
| Exam Center | `apps/portal/exam-center.html` | Launcher for the school's **exam app** (see below) |
| E-Library | `apps/portal/e-library.html` | Launcher for the school's **Calibre** e-book library (see below) |
| Research Hub | `apps/portal/research.html` | Research tools, **offline AI assistant** (LM Studio) + **Wikipedia** (offline Kiwix / online) |
| Parent Portal | `apps/portal/parent-portal.html` | Static demo parent view (internal). **Real per-child access is the standalone parent app — see below** |

The **Parent Portal** and **E-Library** are *also* published as standalone, isolated apps
(`apps/parent/` and `apps/elibrary/`) so they can be forwarded publicly on their own ports without
exposing the rest of the portal. See [Multi-port deployment](#multi-port-deployment--vs-code-tunnel).

## Features

- 🔐 **Sign-in & roles** — `login.html` + `auth.js` gate the portal behind an account. Roles:
  **teacher/admin** (full access, can edit grades), **student** and **parent** (read-only, pinned to
  their own program).
- ✏️ **Editable, saved data** — teachers can edit course scores on the Grades page; changes persist
  per-device in `localStorage` (layered over the seed in `app.js`) and survive reloads.
- 🔔 **Notifications** — the header bell opens a panel to enable browser notifications, send a test,
  and list upcoming items; saving a grade fires a "new grade posted" alert. (Local notifications via
  the service worker — see note below.)
- 📱 **Installable PWA** — `manifest.json` enables add-to-home-screen with app shortcuts
- 🔌 **Offline support** — `sw.js` caches all pages for offline use (cache-first strategy)
- 🎨 Self-contained static HTML — no build step or dependencies required

### Accounts (demo)

Seeded in `auth.js` and stored in the browser. **Demo sign-in only — not real security** (passwords
are checked client-side). For production, move auth and role checks to a backend.

| Username | Password | Role | Sees |
|----------|----------|------|------|
| `teacher` | `teach123` | teacher | everything, can edit grades |
| `admin` | `admin123` | admin | everything, can edit grades |
| `maya` | `maya123` | student | Grade 6 program (read-only) |
| `james` | `james123` | student | GED program (read-only) |
| `parent` | `parent123` | parent | their child's program (read-only) |

### Notifications — local vs. push

Because this is a static site with no backend, it cannot do true **server push** (Web Push needs a
server with VAPID keys). `notify.js` uses the browser Notification API + the service worker to show
**local** notifications while the app is open. To upgrade to real push later, add a backend, generate
VAPID keys, call `registration.pushManager.subscribe()`, and store the subscription server-side.

## E-Library (Calibre)

The E-Library page is a **launcher** for the school's e-book collection, served by
[calibre-web](https://github.com/janeczku/calibre-web) (a web front-end over a Calibre library with an
in-browser reader, logins, and search). Because this portal is a static site, it cannot host the books
itself — calibre-web runs on a separate server and the portal links into it.

**1. Build the library with Calibre desktop.** Install the [Calibre](https://calibre-ebook.com) desktop
app, create a library folder, and **Add books** to it. This produces a `metadata.db` in that folder —
calibre-web serves it.

```powershell
winget install calibre.calibre      # Windows 11 (or download from calibre-ebook.com)
```

```bash
sudo apt install calibre            # Debian/Ubuntu server, if building the library there
```

**2. Run calibre-web** (Docker example) and point `/books` at the library folder from step 1:

```bash
docker run -d --name calibre-web -p 8083:8083 \
  -v /path/to/config:/config \
  -v "C:/calibre-library":/books \
  lscr.io/linuxserver/calibre-web:latest
```

Open `http://<server>:8083`, set the database location to **`/books`** when prompted, then sign in with
the default **`admin` / `admin123`** — **change this immediately** and add student accounts under Admin.

**3. Point the portal at it.** On the E-Library page, open the **Library Server** panel and enter the
calibre-web address (e.g. `http://library.school.local:8083`). It's saved per-device in the browser.
To bake in a default for everyone, set `SCHOLASTICA.libraryUrlDefault` in `shared/app.js`.

Students then tap **Open Library** / a subject / a search to jump straight into calibre-web and read
online or download the EPUB/PDF.

> **⚠️ Use HTTPS in production.** If the portal is served over HTTPS (e.g. GitHub Pages) but calibre-web
> is plain `http://`, browsers block the cross-origin links as **mixed content** and the buttons silently
> fail. Serve calibre-web over HTTPS too — put it behind a reverse proxy (Caddy or nginx) with a TLS
> certificate (e.g. Let's Encrypt), then use the `https://…` address as the Library Server URL. For
> local testing over plain HTTP this isn't an issue.

## Exam Center (exam app)

The Exam Center page is a **launcher** for [ThoHi/exam-test-webapp](https://github.com/ThoHi/exam-test-webapp)
— a separate **Flask** app (Flask-Login + SQLAlchemy/SQLite) with its own login and admin/teacher/student
roles, exam-taking, results, and grading. Like the E-Library, the portal links into it rather than hosting
it; it runs as its own service on **port 8084**.

**1. Clone it next to this repo** (so the compose build context `../exam-test-webapp` resolves):

```bash
git clone https://github.com/ThoHi/exam-test-webapp ../exam-test-webapp
docker compose up -d exam      # or `docker compose up -d` to start everything
```

**2. Point the portal at it.** On the Exam Center page, open the **Exam Server** panel and enter the exam
app's address (e.g. `http://exams.school.local:8084`). It's saved per-device. To bake in a default for
everyone, set `SCHOLASTICA.examUrlDefault` in `shared/app.js`.

**3. Link results to the parent portal.** When a teacher/admin registers a student in the exam app, set
their **username = the student ID** used in the student database (e.g. `maya`). Their exam scores then
appear in that child's parent portal automatically — see
[Exam results in the parent portal](#exam-results-in-the-parent-portal). This uses a new service
endpoint, `GET /api/student-results/<username>` (requires the `X-Service-Token` header == the exam app's
`SERVICE_TOKEN`). **Note:** this endpoint is an addition to the exam-test-webapp project — commit/push it
in that repo too.

> **⚠️ Harden before exposing it publicly.** The exam app currently runs Flask with `debug=True` and a
> hard-coded `SECRET_KEY = 'change-this-secret'` (see its `app.py`). Before forwarding port 8084 through a
> tunnel, set a real secret (ideally from an env var), turn off debug, and serve it via a WSGI server
> (gunicorn) behind HTTPS. Its login is **separate** from the portal's — students sign in to the exam app
> directly. The SQLite database is persisted by the `exam-data` volume in `docker-compose.yml`.

## Parent Portal — per-child access (student API)

The standalone **parent app** (`apps/parent/`, port **8081**) is backed by a real **student API**
(`backend/`, a small Flask service on port **8085**) — the authoritative student database. Each parent
is linked to exactly one student, and **the server returns only that child's report**: a request for
another student gets **403**, so student B's data never reaches parent A's browser.

This is different from the portal's client-side demo accounts: there, all data ships to every browser
and access is UI-only. Here the check is on the server, so it is **real isolation**.

```
Parent app (8081)  ──login──▶  Student API (8085)  ──▶  SQLite (students, users)
   renders report   ◀─token──     authorizes by             parent → one student
                                   parent↔student link
```

**Accounts** (seeded in `backend/app.py`):

| Username | Password | Role | Sees |
|----------|----------|------|------|
| `parent_maya` | `parent123` | parent | **only** Maya's report |
| `parent_james` | `parent123` | parent | **only** James's report |
| `maya` / `james` | `maya123` / `james123` | student | only their own report |
| `teacher` / `admin` | `teach123` / `admin123` | staff | any student |

**Use it:** `docker compose up -d --build api parent`, open <http://localhost:8081>, sign in as
`parent_maya`. The app calls `http://localhost:8085`; change it under *Advanced* on the login screen
(saved per-device) or via `SECRET_KEY`/ports in `docker-compose.yml`. Set a real `SECRET_KEY` for the
`api` service before production.

**API endpoints:** `POST /api/login` · `GET /api/me` · `GET /api/my-report` · `GET /api/students`
(staff only) · `GET /api/students/<id>` (authorized only). Token-based (`Authorization: Bearer …`).

### Exam results in the parent portal

Each student's report also includes their **exam results from the exam app** (see
[Exam Center](#exam-center-exam-app)). The student API fetches them **server-to-server** and merges
them into the report, so the parent sees them under *Exam Results*:

```
Parent app ─▶ Student API ──(X-Service-Token)──▶ Exam app  /api/student-results/<id>
                          merges report.exams ◀──            (Grade rows for that student)
```

**The link key is the student ID = the exam-app username.** So when a teacher registers a student in
the exam app, use the **same ID** as in the student database (e.g. `maya`). That student's scores then
appear automatically in their parent's portal. The two services share a secret: the exam app's
`SERVICE_TOKEN` must equal the API's `EXAM_SERVICE_TOKEN` (set in `docker-compose.yml`). If the exam
app is down, the report still loads — just without exam results.

## Research Hub — offline AI assistant (LM Studio)

The Research page has an **AI Research Assistant** chat that runs entirely **offline** against a local
[LM Studio](https://lmstudio.ai) model — no internet, no cloud, nothing leaves the device. LM Studio
exposes an **OpenAI-compatible** server, and the page streams chat completions from it.

**1. Install LM Studio** and download a small **Gemma** model (there is no "Gemma 4" — the current
small one is **Gemma 3 4B Instruct**; `gemma-3-4b` is the default model id the page uses).

```powershell
winget install ElementLabs.LMStudio    # Windows 11 (or download from lmstudio.ai)
```

**2. Start the local server.** In LM Studio → **Developer** (Local Server) tab → load the Gemma model →
**Start Server** (default `http://localhost:1234`). **Enable CORS** in the server settings — without it
the browser blocks the page's requests.

**3. Use it.** Open the Research page → the **AI Research Assistant** card. Click the ⚙️ settings to set
the server (`http://localhost:1234/v1`) and **Test** to auto-detect the loaded model, then chat. The
defaults live in `shared/app.js` (`SCHOLASTICA.llmUrlDefault`, `SCHOLASTICA.llmModelDefault`).

> **Offline only.** Because the model is at plain `http://localhost:1234`, use the Research page over
> **`http://localhost:8080`** (local). If you serve the portal over an **HTTPS** tunnel, the browser
> blocks the call to `http://localhost` as mixed content — the assistant is meant for on-site/offline
> use. The status dot turns green when connected, red with a hint when LM Studio isn't reachable.

## AI proxy — local-first LLM with cloud fallback

For the school server you can run **one shared model** instead of per-device LM Studio. The `ai-proxy`
service (`ai-proxy/`, port **8087**) is an OpenAI-compatible endpoint that **tries a local model first
and falls back to a cloud API when local is down** — and the cloud key stays server-side, never in the
browser.

```
Research page ─▶ ai-proxy (8087) ──▶ LOCAL  (Ollama / LM Studio)   ✅ free, offline
                  holds cloud key  └▶ CLOUD  (OpenAI-compatible)    ☁️ fallback
```

**1. Run a local model** — [Ollama](https://ollama.com) is easiest on a server:

```bash
ollama serve            # OpenAI API at http://localhost:11434/v1
ollama pull phi3:mini   # or gemma2:2b, qwen2.5:3b … (English-only is fine here)
```

**2. Configure the proxy** in `docker-compose.yml` (the `ai-proxy` service):
- `LOCAL_API_URL` — `http://host.docker.internal:11434/v1` (Ollama on host) or `…:1234/v1` (LM Studio).
- Cloud fallback is **off until you set** `CLOUD_API_URL` + `CLOUD_API_KEY` + `CLOUD_MODEL`. Any
  OpenAI-compatible API works by URL+key, e.g. OpenAI (`https://api.openai.com/v1`) or OpenRouter
  (`https://openrouter.ai/api/v1`). (Anthropic's native API needs a small adapter — hook noted in
  `ai-proxy/app.py`.)
- `MAX_CONCURRENCY=1` — CPU does ~1 inference at a time; the proxy serializes requests (a simple queue).

```bash
docker compose up -d --build ai-proxy
```

**3. Point the Research assistant at it** — on the Research page, open the AI assistant ⚙️ and set the
server to `http://localhost:8087/v1`. Streaming, `/v1/models`, and graceful "no backend available"
errors all work; `GET /health` shows which backend is live.

## AI Notebook — "ask my school notes" (RAG)

`ai-notebook` (port **8088**) lets students ask questions answered from the school's own notes, not the
model's imagination. A teacher uploads notes/PDFs; each question retrieves the most relevant passages
and the answer is grounded in them, with sources.

```
question → embed (Ollama) → top-K similar chunks (local vector store) → inject into prompt
        → answer streamed via the ai-proxy (local-first + cloud fallback)
```

- **Embeddings:** Ollama (`EMBED_MODEL`, default `nomic-embed-text`) — `ollama pull nomic-embed-text`.
- **Vector store:** a tiny built-in store (SQLite + numpy cosine) — instant at a school's scale and
  dependency-light; swap in ChromaDB only if the corpus grows huge.
- **Generation:** delegated to the [ai-proxy](#ai-proxy--local-first-llm-with-cloud-fallback), so it
  reuses local-first + cloud fallback + the single-inference queue.

**Use it:**

```bash
ollama pull nomic-embed-text          # embeddings model (plus a chat model for the proxy)
docker compose up -d --build ai-notebook
```

Open <http://localhost:8088> → **Teacher** → enter the admin token (`ADMIN_TOKEN` in
`docker-compose.yml`, default `change-me-notebook-admin`) → upload `.pdf`/`.txt`/`.md` notes. Students
then ask questions in the chat; if nothing is uploaded yet, or a model is missing, it says so clearly.
`GET /health` shows doc/chunk counts and whether Ollama + the proxy are reachable.

> Uploads are gated by the admin token; student chat is open on the LAN. For attributable per-student
> use, put it behind the portal/login later. The notes DB is persisted in the `notebook-data` volume.

## Offline Wikipedia (Kiwix) — English / Burmese / Shan

The Research page has a **Wikipedia** tool that **first checks for a local offline library** and falls
back to online `wikipedia.org` if none is found. Offline Wikipedia is served by
[Kiwix](https://kiwix.org) from **ZIM** files. The page probes `http://localhost:8086`; the language
selector covers **English, Burmese (my), and Shan (shn)**.

**1. Download ZIM files** for the three languages from
<https://download.kiwix.org/zim/wikipedia/> into `./wikipedia/zim/` (filenames include a date, so pick
the latest). Smaller `nopic`/`mini` variants are far smaller than the full `maxi` ones:

| Language | Code | File pattern |
|----------|------|--------------|
| English | `en` | `wikipedia_en_all_nopic.zim` (or `_mini` / `_maxi`) |
| Burmese | `my` | `wikipedia_my_all_maxi.zim` (or `_nopic`) |
| Shan | `shn` | `wikipedia_shn_all_maxi.zim` (or `_nopic`) |

```bash
mkdir -p wikipedia/zim
cd wikipedia/zim
# example — check the directory for the current dated filename first:
curl -O https://download.kiwix.org/zim/wikipedia/wikipedia_en_all_nopic.zim
curl -O https://download.kiwix.org/zim/wikipedia/wikipedia_my_all_maxi.zim
curl -O https://download.kiwix.org/zim/wikipedia/wikipedia_shn_all_maxi.zim
```

**2. Start the Kiwix server** (opt-in profile, since the ZIMs are large):

```bash
docker compose --profile wiki up -d wikipedia    # serves all *.zim on port 8086
```

**3. Use it.** Open the Research page → **Wikipedia**: the status dot turns green ("Offline library
available") and searches open in Kiwix offline. With the server stopped, it shows "using online
Wikipedia" and searches open `en/my/shn.wikipedia.org`. Set the server URL under ⚙️ (default
`http://localhost:8086`; `SCHOLASTICA.wikiUrlDefault` in `shared/app.js`).

> ZIM files are **not** committed (git-ignored). Offline reads need the portal over
> `http://localhost:8080`; over an HTTPS tunnel the `http://localhost:8086` call is blocked as mixed
> content (same as the AI assistant) — offline Wikipedia is for on-site use.

## Project structure

The portal is split into **three independent apps**, each served on its own port. Shared JavaScript
and the icon live once in `shared/`; each app's image copies `shared/` plus that app's own files into
the nginx web root at **build time** (`Dockerfile.static`), so there is a single source of truth.

```
school portal/
├── shared/                 # single source — copied into every app image at build
│   ├── app.js              #   program data, grading helpers, localStorage persistence
│   ├── auth.js             #   sign-in, roles, route guard (loaded in <head> everywhere)
│   ├── notify.js           #   local notifications + header bell
│   └── icon.svg            #   app icon
├── apps/
│   ├── portal/             # FULL app  → port 8080  (students / teachers — keep internal)
│   │   ├── index.html · login.html · attendance.html · grades.html
│   │   ├── exam-center.html · e-library.html · research.html · parent-portal.html
│   │   ├── manifest.json · sw.js
│   ├── parent/             # standalone Parent Portal → port 8081 (API-driven; own login)
│   │   └── index.html · manifest.json · sw.js
│   └── elibrary/           # standalone E-Library launcher → port 8082
│       └── index.html · login.html · manifest.json · sw.js
├── backend/                # Flask student API → port 8085 (authoritative student DB)
│   ├── app.py · requirements.txt · Dockerfile
├── ai-proxy/               # FastAPI LLM proxy → port 8087 (local-first + cloud fallback)
│   ├── app.py · requirements.txt · Dockerfile
├── ai-notebook/            # FastAPI RAG "ask my school notes" → port 8088
│   ├── app.py · static/index.html · requirements.txt · Dockerfile
├── Dockerfile.static       # builds a static app image (shared/ + one app) for portal/parent/elibrary
├── docker-compose.yml      # portal 8080 · parent 8081 · elibrary 8082 · exam 8084 · api 8085
└── README.md
```

**Isolation is physical:** each app's container only contains its own pages, so the parent/e-library
ports cannot reach `grades.html` etc. even by guessing URLs. The apps are separate origins, so each
has its own login session.

## Running locally (Docker)

```bash
docker compose up -d --build   # build & start every app
docker compose up -d --build   # also the command to re-run after editing any file
docker compose down            # stop
```

Then open:

| App | URL | For |
|-----|-----|-----|
| Main portal | <http://localhost:8080> | students & teachers (internal) |
| Parent portal | <http://localhost:8081> | parents (needs the **student API** on 8085) |
| E-Library | <http://localhost:8082> | library launcher |
| Exam app | <http://localhost:8084> | exams (separate Flask app — clone `../exam-test-webapp` first) |
| Student API | <http://localhost:8085> | backend for the parent app (per-child reports) |
| AI proxy | <http://localhost:8087> | local-first LLM + cloud fallback for the Research chat |
| AI Notebook | <http://localhost:8088> | RAG — students ask questions answered from school notes |

> The `exam` service builds from `../exam-test-webapp`; clone that repo next to this one or run
> `docker compose up -d portal parent elibrary` to skip it. calibre-web (for the E-Library) runs on
> **8083** as its own container (see [E-Library](#e-library-calibre)).

> Static files are **copied into the image at build time**, so re-run with `--build` after editing any
> page or shared script. Service workers also cache aggressively — hard-reload (or bump the `CACHE`
> version in the app's `sw.js`) if you don't see a change.

## Multi-port deployment & VS Code tunnel

To reach the school server from a public browser, forward the ports with a
[VS Code tunnel](https://code.visualstudio.com/docs/remote/tunnels):

1. On the server: `docker compose up -d`, then `code tunnel` (or **Ports** panel → *Forward a Port*).
2. Forward the ports you want public — typically **8081** (parents), **8082** (e-library), **8083**
   (calibre-web), and **8084** (exam app). Keep **8080** (full portal) unforwarded / internal.
3. Each forwarded port gets its own public `https://…devtunnels.ms` URL. Set port **visibility** to
   *Public* only for the ports you intend to share.

Because tunnels serve over **HTTPS**, point the E-Library's *Library Server* URL **and** the Exam
Center's *Exam Server* URL at **HTTPS** addresses (the forwarded `https://…devtunnels.ms` URLs work),
or the cross-origin links are blocked as mixed content. Also harden the exam app before exposing it
(see [Exam Center](#exam-center-exam-app)).

## Remote access (setup & maintenance)

To administer the server remotely — edit files, restart containers, tail logs — use a **VS Code Remote
Tunnel**. It gives a browser-based editor **+ integrated terminal + port forwarding**, authenticated by
your GitHub/Microsoft account, with **no inbound firewall ports opened**.

**On the server** (one-time, in an interactive PowerShell — it prompts for a device login):

```powershell
code tunnel service install     # runs as a background service, starts at login
# or: code tunnel               # foreground, to test first
```

Authenticate with GitHub/Microsoft and name the machine (e.g. `school-server`).

**From anywhere**, open `https://vscode.dev/tunnel/school-server`, sign in with the **same account**,
then use the Terminal to manage the stack:

```bash
cd "/c/Users/lenovo/code_hub/school portal"
docker compose ps                 # status
docker compose up -d --build      # apply changes after editing files
docker compose logs -f exam       # tail a service
```

Service control: `code tunnel service status` · `code tunnel service uninstall`.

**Separate the two concerns:**

| Need | Audience | How |
|------|----------|-----|
| **Admin / maintenance** (terminal, edit, restart) | just you | VS Code tunnel — account-authenticated, keep 2FA on |
| **App access** (open the portal) | students / parents | tunnel **port forwarding** set to *Public* (8081/8082/8084) |

The machine must stay **on and signed in** (and Docker Desktop running) for both the apps and the tunnel
service. For full OS-level access (RDP / SSH), put the machine on a private mesh with
[Tailscale](https://tailscale.com) (`winget install tailscale.tailscale`) instead of exposing those
ports publicly.

## Updating the offline cache

Each app has its own `sw.js`. When you add or rename a page in an app, update **both**:

1. The `PAGES` array in that app's `sw.js`
2. The `CACHE` version string in that `sw.js` so clients fetch the new files

## Security

**Secrets live in a git-ignored `.env`.** Copy `.env.example` → `.env` and set strong random values
(`python -c "import secrets;print(secrets.token_urlsafe(32))"`) for `API_SECRET_KEY`,
`EXAM_SERVICE_TOKEN`, and `NOTEBOOK_ADMIN_TOKEN`. docker-compose reads `.env` automatically. The
student-API secret **must** be strong, or session tokens can be forged.

Hardening already applied:

- **Exam app:** the Werkzeug debugger is **off** by default (`FLASK_DEBUG=1` enables it locally only —
  it allows remote code execution); the previously **public** grades CSV now requires a signed-in
  teacher/admin.
- **AI proxy:** optional `PROXY_TOKEN` so it isn't an open relay to your cloud key. Empty = open (fine
  on a trusted LAN where the browser Research chat needs no token); **set it** once a cloud key is
  configured or the port is exposed. Browser clients would expose the token, so keep a cloud-backed,
  token-protected proxy **off** the public network and let server-side callers (ai-notebook) use it.
- **AI Notebook:** uploads limited to `MAX_UPLOAD_MB` (default 20) and `.pdf/.txt/.md`; admin token
  compared in constant time.
- **Static apps:** baseline headers — `X-Frame-Options`, `X-Content-Type-Options`, `Referrer-Policy`,
  and a CSP (in `nginx/default.conf`).

Still your responsibility before exposing anything publicly:

- **Keep port 8080 (main portal) internal — do not tunnel it.** Its sign-in is client-side demo auth
  (passwords are in the page and all data ships to the browser). Only the **parent portal (8081)**,
  whose access is enforced by the student API, is safe to share.
- **Replace the demo passwords** and add **login rate-limiting** (the API/exam logins currently have
  none → brute-forceable).
- **Serve over HTTPS/TLS** beyond a trusted LAN (e.g. a [Caddy](https://caddyserver.com) reverse proxy
  for automatic certificates), set a real `SECRET_KEY` for the exam app, and run it under gunicorn.
- **Restrict CORS** to known origins, and review each **AI model**'s own license/terms before deploying.

## License

This project's own code is licensed under the **[PolyForm Noncommercial License 1.0.0](LICENSE)**.

- ✅ **Free** to use, modify, and share for any **non-commercial** purpose — schools, universities,
  nonprofits, government, research, and personal/hobby use.
- 🚫 **Not for commercial use** — you may not use it for commercial advantage or monetary compensation
  (e.g. selling it, or running it as part of a for-profit product/service) without a separate license.
- Keep the copyright/`Required Notice` line if you redistribute (see `LICENSE`).

**Third-party components keep their own licenses.** This repository only licenses the original code
here. Bundled or required tools — Flask, FastAPI, Tailwind, Material Symbols, Kiwix, calibre-web, the
exam app, Ollama, etc. — and especially any **AI models** you run (e.g. **Gemma** under the Gemma Terms
of Use, **Phi-3** under MIT, **Qwen** under its license) are governed by **their own terms**, which this
license does not override. Review a model's license before deploying it, particularly for anything
beyond personal/educational use.

> Want to allow some commercial use later (e.g. paid support) or need a commercial license yourself?
> The copyright holder can dual-license or grant exceptions — that's your call as the author.
