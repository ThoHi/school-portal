# Scholastica — Academic Excellence Portal

A unified school management portal for **students, teachers, and parents**, built as an installable
[Progressive Web App (PWA)](https://web.dev/progressive-web-apps/). It works offline and can be added
to a phone or desktop home screen.

## Pages

| Page | File | Description |
|------|------|-------------|
| Dashboard | `index.html` | Main landing dashboard and navigation hub |
| Exam Center | `exam-center.html` | Exams, schedules, and results |
| E-Library | `e-library.html` | Digital library of learning resources |
| Research Hub | `research.html` | Research materials and tools |
| Parent Portal | `parent-portal.html` | Parent view of student progress |

## Features

- 📱 **Installable PWA** — `manifest.json` enables add-to-home-screen with app shortcuts
- 🔌 **Offline support** — `sw.js` caches all pages for offline use (cache-first strategy)
- 🎨 Self-contained static HTML — no build step or dependencies required

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
