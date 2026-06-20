# Scholastica — Academic Excellence Portal

A unified school management portal for **students, teachers, and parents**, built as an installable
[Progressive Web App (PWA)](https://web.dev/progressive-web-apps/). It works offline and can be added
to a phone or desktop home screen.

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
| Research Hub | `apps/portal/research.html` | Research materials and tools |
| Parent Portal | `apps/portal/parent-portal.html` | Parent view of student progress |

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

**1. Run calibre-web** (Docker example):

```bash
docker run -d --name calibre-web -p 8083:8083 \
  -v /path/to/config:/config \
  -v /path/to/calibre-library:/books \
  lscr.io/linuxserver/calibre-web:latest
```

Point `/books` at a folder containing a Calibre library (a `metadata.db` created by the Calibre desktop
app). Open `http://<server>:8083`, complete setup, and add student accounts.

**2. Point the portal at it.** On the E-Library page, open the **Library Server** panel and enter the
calibre-web address (e.g. `http://library.school.local:8083`). It's saved per-device in the browser.
To bake in a default for everyone, set `SCHOLASTICA.libraryUrlDefault` in `app.js`.

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

> **⚠️ Harden before exposing it publicly.** The exam app currently runs Flask with `debug=True` and a
> hard-coded `SECRET_KEY = 'change-this-secret'` (see its `app.py`). Before forwarding port 8084 through a
> tunnel, set a real secret (ideally from an env var), turn off debug, and serve it via a WSGI server
> (gunicorn) behind HTTPS. Its login is **separate** from the portal's — students sign in to the exam app
> directly. The SQLite database is persisted by the `exam-data` volume in `docker-compose.yml`.

## Project structure

The portal is split into **three independent apps**, each served on its own port. Shared JavaScript
and the icon live once in `shared/` and are mounted into each app's web root at runtime, so there is a
single source of truth.

```
school portal/
├── shared/                 # single source for assets mounted into every app
│   ├── app.js              #   program data, grading helpers, localStorage persistence
│   ├── auth.js             #   sign-in, roles, route guard (loaded in <head> everywhere)
│   ├── notify.js           #   local notifications + header bell
│   └── icon.svg            #   app icon
├── apps/
│   ├── portal/             # FULL app  → port 8080  (students / teachers — keep internal)
│   │   ├── index.html · login.html · attendance.html · grades.html
│   │   ├── exam-center.html · e-library.html · research.html · parent-portal.html
│   │   ├── manifest.json · sw.js
│   ├── parent/             # standalone Parent Portal → port 8081 (safe to forward publicly)
│   │   └── index.html · login.html · manifest.json · sw.js
│   └── elibrary/           # standalone E-Library launcher → port 8082
│       └── index.html · login.html · manifest.json · sw.js
├── docker-compose.yml      # three nginx services on 8080 / 8081 / 8082
└── README.md
```

**Isolation is physical:** each app's container only contains its own pages, so the parent/e-library
ports cannot reach `grades.html` etc. even by guessing URLs. The apps are separate origins, so each
has its own login session.

## Running locally (Docker)

```bash
docker compose up -d      # build & start every app
docker compose down       # stop
```

Then open:

| App | URL | For |
|-----|-----|-----|
| Main portal | <http://localhost:8080> | students & teachers (internal) |
| Parent portal | <http://localhost:8081> | parents |
| E-Library | <http://localhost:8082> | library launcher |
| Exam app | <http://localhost:8084> | exams (separate Flask app — clone `../exam-test-webapp` first) |

> The `exam` service builds from `../exam-test-webapp`; clone that repo next to this one or run
> `docker compose up -d portal parent elibrary` to skip it. calibre-web (for the E-Library) runs on
> **8083** as its own container (see [E-Library](#e-library-calibre)).

> Service workers need HTTP (not `file://`), which nginx provides. To preview a single static app
> without Docker you can run `python -m http.server` inside an app folder, but the `shared/` assets
> won't be present — Docker (or copying `shared/*` in) is the supported path.

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

## Updating the offline cache

Each app has its own `sw.js`. When you add or rename a page in an app, update **both**:

1. The `PAGES` array in that app's `sw.js`
2. The `CACHE` version string in that `sw.js` so clients fetch the new files
