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

| Page | File | Description |
|------|------|-------------|
| Dashboard | `index.html` | Main landing dashboard and navigation hub |
| Attendance | `attendance.html` | Attendance tracking — rates by course, calendar heatmap, activity log |
| Grades | `grades.html` | Grades & GPA — per-course grades, weighted GPA, trend chart by semester |
| Exam Center | `exam-center.html` | Exams, schedules, and results |
| E-Library | `e-library.html` | Launcher for the school's **Calibre** e-book library (see below) |
| Research Hub | `research.html` | Research materials and tools |
| Parent Portal | `parent-portal.html` | Parent view of student progress |

## Features

- 📱 **Installable PWA** — `manifest.json` enables add-to-home-screen with app shortcuts
- 🔌 **Offline support** — `sw.js` caches all pages for offline use (cache-first strategy)
- 🎨 Self-contained static HTML — no build step or dependencies required

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

## Running locally

The site is plain static HTML, but service workers require it to be served over HTTP
(not opened via `file://`). Use any static server:

```bash
# Python
python -m http.server 8000

# Node (npx)
npx serve .
```

Then open <http://localhost:8000>.

## Project structure

```
school portal/
├── index.html          # Dashboard
├── exam-center.html    # Exam Center
├── e-library.html      # E-Library
├── research.html       # Research Hub
├── parent-portal.html  # Parent Portal
├── manifest.json       # PWA manifest
├── sw.js               # Service worker (offline caching)
└── icon.svg            # App icon
```

## Updating the offline cache

When you add or rename a page, update **both**:

1. The `PAGES` array in `sw.js`
2. The cache version (`scholastica-v1`) in `sw.js` so clients fetch the new files
