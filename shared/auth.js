/* Scholastica Portal — client-side auth, roles & route guard.

   ⚠️ This is DEMO authentication for a static, backend-less PWA. Accounts and
   passwords live in the browser and are checked client-side, so it gates the UI
   but is NOT real security. For a real deployment, move auth to a server
   (e.g. Supabase/Firebase) and verify roles on the backend.

   Roles:
     - teacher / admin : full access, can EDIT grades & attendance
     - student         : read-only view of their own track
     - parent          : read-only view of their child's track

   This file is loaded in <head> on every page so the guard runs before the
   page renders. login.html is exempt. */
(function () {
  "use strict";

  const SESSION_KEY = "scholastica-session";
  const USERS_KEY = "scholastica-users-v1";
  const TRACK_KEY = "scholastica-track"; // shared with app.js

  // Seed accounts. Stored in localStorage on first run so an admin could add
  // more later. Passwords are demo-only (see warning above).
  const SEED_USERS = [
    { username: "teacher", password: "teach123", role: "teacher", name: "Ms. Rivera",  initials: "MR", track: null },
    { username: "admin",   password: "admin123", role: "admin",   name: "Principal Hale", initials: "PH", track: null },
    { username: "maya",    password: "maya123",  role: "student", name: "Maya Chen",   initials: "MC", track: "primary" },
    { username: "james",   password: "james123", role: "student", name: "James Carter", initials: "JC", track: "ged" },
    { username: "parent",  password: "parent123", role: "parent", name: "R. Chen",      initials: "RC", track: "primary" },
  ];

  function loadUsers() {
    try {
      const saved = JSON.parse(localStorage.getItem(USERS_KEY));
      if (Array.isArray(saved) && saved.length) return saved;
    } catch (_) { /* fall through to seed */ }
    localStorage.setItem(USERS_KEY, JSON.stringify(SEED_USERS));
    return SEED_USERS;
  }

  function getSession() {
    try { return JSON.parse(localStorage.getItem(SESSION_KEY)); } catch (_) { return null; }
  }

  function login(username, password) {
    const u = loadUsers().find(
      x => x.username.toLowerCase() === String(username).trim().toLowerCase() && x.password === password
    );
    if (!u) return { ok: false, error: "Incorrect username or password." };
    const session = { username: u.username, role: u.role, name: u.name, initials: u.initials, track: u.track, ts: Date.now() };
    localStorage.setItem(SESSION_KEY, JSON.stringify(session));
    // Students/parents are pinned to their own track.
    if (u.track) localStorage.setItem(TRACK_KEY, u.track);
    return { ok: true, session };
  }

  function logout() {
    localStorage.removeItem(SESSION_KEY);
    location.href = "login.html";
  }

  const EDIT_ROLES = ["teacher", "admin"];
  function canEdit() {
    const s = getSession();
    return !!s && EDIT_ROLES.indexOf(s.role) !== -1;
  }
  function hasRole() {
    const s = getSession();
    if (!s) return false;
    for (let i = 0; i < arguments.length; i++) if (s.role === arguments[i]) return true;
    return false;
  }

  const onLoginPage = /(^|\/)login\.html$/.test(location.pathname) || location.pathname.endsWith("/login.html");

  // --- route guard: run immediately (head script) ---
  if (!onLoginPage && !getSession()) {
    location.replace("login.html");
    return;
  }

  // --- header wiring: runs once DOM is ready ---
  function wireHeader() {
    const s = getSession();
    if (!s) return;

    // Avatar initials (replace the demo photo if present).
    document.querySelectorAll("[data-avatar-initials]").forEach(n => { n.textContent = s.initials; });
    document.querySelectorAll("[data-user-name]").forEach(n => { n.textContent = s.name; });
    document.querySelectorAll("[data-user-role]").forEach(n => { n.textContent = s.role; });

    // If a page still shows the stock <img> avatar, swap it for initials.
    document.querySelectorAll(".h-8.w-8.rounded-full img, .h-8.w-8.rounded-full > img").forEach(img => {
      const holder = img.parentElement;
      holder.innerHTML = "";
      holder.classList.add("flex", "items-center", "justify-center", "text-on-primary", "font-label-md", "text-label-md");
      holder.setAttribute("data-avatar-initials", "");
      holder.textContent = s.initials;
    });

    // Wire any "Logout" links/buttons.
    document.querySelectorAll("a, button").forEach(el => {
      if (/logout/i.test(el.textContent || "")) {
        el.addEventListener("click", e => { e.preventDefault(); logout(); });
      }
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", wireHeader);
  } else {
    wireHeader();
  }

  // Public API
  window.Auth = {
    getSession, login, logout, canEdit, hasRole, loadUsers,
    SEED_USERS,
  };
})();
