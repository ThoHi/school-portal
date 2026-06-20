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
| 👪 **Parent portal** | http://localhost:8081 | Standalone parent view (safe to share) |
| 📚 **E-Library** | http://localhost:8082 | Launcher for the Calibre library |
| 📝 **Exam app** | http://localhost:8084 | Separate Flask exam system (its own login) |

Over a VS Code tunnel, replace `localhost:<port>` with each forwarded `https://…devtunnels.ms` URL.

## Portal accounts (8080 / 8081)

Sign in at any portal app. The **same account works** on the main portal and the parent portal
(each port is a separate login session, so sign in on each).

| Username | Password | Role | What they can do |
|----------|----------|------|------------------|
| `teacher` | `teach123` | Teacher | Everything + **edit grades** on the Grades page |
| `admin` | `admin123` | Admin | Everything + edit grades |
| `maya` | `maya123` | Student | Read-only — Grade 6 program |
| `james` | `james123` | Student | Read-only — GED program |
| `parent` | `parent123` | Parent | Read-only — their child's program |

**Demo flow:** sign in as `teacher` on 8080 → **Grades** → **Edit** → change a score → **Save**
(fires a "new grade posted" notification). Then sign in as `maya` to see the read-only student view.

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
