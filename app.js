/* Scholastica Portal — shared program data & helpers
   The school runs two programs:
     - primary : elementary Grade 5/6 (letter + percentage grading)
     - ged     : GED prep (official 100–200 score scale, 145 = pass)
   The selected track is stored in localStorage and shared across pages. */

const SCHOLASTICA = {
  tracks: {
    primary: {
      id: "primary",
      label: "Grade 5/6",
      term: "Term 2 · 2025–26",
      grading: "letter",
      student: { name: "Maya", fullName: "Maya Chen", grade: "Grade 6 · Room 6B", initials: "MC" },
      // score = percentage; attended/total = class sessions this term
      subjects: [
        { name: "Mathematics",          code: "Gr6 · Math", score: 92, attended: 56, total: 58, trend: "up" },
        { name: "English Language Arts", code: "Gr6 · ELA",  score: 88, attended: 57, total: 58, trend: "flat" },
        { name: "Science",              code: "Gr6 · Sci",  score: 95, attended: 55, total: 58, trend: "up" },
        { name: "Social Studies",       code: "Gr6 · SS",   score: 84, attended: 54, total: 58, trend: "down" },
        { name: "Reading",              code: "Gr6 · Read", score: 90, attended: 58, total: 58, trend: "up" },
        { name: "Art",                  code: "Gr6 · Art",  score: 97, attended: 28, total: 29, trend: "up" },
        { name: "Physical Education",   code: "Gr6 · PE",   score: 93, attended: 27, total: 29, trend: "flat" },
      ],
      // progress over reporting periods (percentages)
      trend: [
        { term: "Q1", value: 85 }, { term: "Q2", value: 87 },
        { term: "Q3", value: 89 }, { term: "Q4", value: 91 },
      ],
      schedule: [
        { time: "08:30", subject: "Mathematics",          room: "Room 6B · Ms. Rivera",     state: "done" },
        { time: "09:45", subject: "English Language Arts", room: "Room 6B · Mr. Adeyemi",    state: "now" },
        { time: "11:15", subject: "Science",              room: "Lab 2 · Ms. Tan",          state: "next" },
        { time: "13:00", subject: "Physical Education",   room: "Gymnasium · Coach Brooks", state: "next" },
        { time: "14:15", subject: "Art",                  room: "Art Room · Ms. Lopez",     state: "next" },
      ],
      upcoming: [
        { subject: "Math Unit Quiz",        when: "Tomorrow, 9:00 AM",  icon: "calculate" },
        { subject: "Science Fair Project",  when: "Fri, Jun 19",        icon: "science" },
        { subject: "Reading Comprehension", when: "Mon, Jun 22",        icon: "menu_book" },
      ],
      achievement: { tag: "Recognition", title: "Honor Roll", note: "Great work! Maya kept a term average above 90% — she's on the Grade 6 Honor Roll." },
    },

    ged: {
      id: "ged",
      label: "GED",
      term: "GED Prep · Spring Cohort",
      grading: "ged",
      student: { name: "James", fullName: "James Carter", grade: "GED Prep · Evening", initials: "JC" },
      // score = practice-test score on the 100–200 GED scale; 145 = pass
      subjects: [
        { name: "Mathematical Reasoning",          code: "GED · Math", score: 158, attended: 22, total: 24, trend: "up" },
        { name: "Reasoning Through Language Arts",  code: "GED · RLA",  score: 165, attended: 23, total: 24, trend: "up" },
        { name: "Science",                         code: "GED · Sci",  score: 149, attended: 21, total: 24, trend: "flat" },
        { name: "Social Studies",                  code: "GED · SS",   score: 152, attended: 20, total: 24, trend: "up" },
      ],
      // average practice-test score over time (100–200 scale)
      trend: [
        { term: "Test 1", value: 138 }, { term: "Test 2", value: 146 },
        { term: "Test 3", value: 152 }, { term: "Test 4", value: 156 },
      ],
      schedule: [
        { time: "17:30", subject: "Mathematical Reasoning",         room: "Room A · Mr. Daniels", state: "done" },
        { time: "18:45", subject: "Reasoning Through Language Arts", room: "Room A · Ms. Owens",   state: "now" },
        { time: "20:00", subject: "Science",                        room: "Room B · Dr. Petrov",  state: "next" },
      ],
      upcoming: [
        { subject: "GED Math Practice Test", when: "Thu, Jun 18",  icon: "calculate" },
        { subject: "RLA Essay Workshop",     when: "Tue, Jun 23",  icon: "edit_note" },
        { subject: "Official GED — Science", when: "Mon, Jul 6",   icon: "verified" },
      ],
      achievement: { tag: "Test Readiness", title: "3 of 4 Passing", note: "James is passing 3 of the 4 GED subjects. One more — Science — to be test-ready across the board." },
    },
  },
};

/* ---------- track state ---------- */
const TRACK_KEY = "scholastica-track";
function getTrackId() {
  const id = localStorage.getItem(TRACK_KEY);
  return SCHOLASTICA.tracks[id] ? id : "primary";
}
function getTrack() { return SCHOLASTICA.tracks[getTrackId()]; }
function setTrack(id) {
  if (!SCHOLASTICA.tracks[id]) return;
  localStorage.setItem(TRACK_KEY, id);
  document.dispatchEvent(new CustomEvent("trackchange", { detail: { id } }));
}

/* ---------- grading helpers ---------- */
function letterFromPct(p) {
  if (p >= 93) return "A";
  if (p >= 90) return "A-";
  if (p >= 87) return "B+";
  if (p >= 83) return "B";
  if (p >= 80) return "B-";
  if (p >= 77) return "C+";
  if (p >= 73) return "C";
  if (p >= 70) return "C-";
  if (p >= 65) return "D";
  return "F";
}
function letterBadge(letter) {
  if (letter.startsWith("A")) return "bg-success-container text-success";
  if (letter.startsWith("B")) return "bg-secondary-container text-on-secondary-container";
  if (letter.startsWith("C")) return "bg-tertiary-fixed text-on-tertiary-container";
  return "bg-error-container text-error";
}
// GED 100–200 scale bands
function gedBand(score) {
  if (score >= 175) return { label: "Honors",        text: "text-tertiary",  badge: "bg-tertiary-fixed text-on-tertiary-container", bar: "bg-tertiary" };
  if (score >= 165) return { label: "College Ready", text: "text-secondary", badge: "bg-secondary-container text-on-secondary-container", bar: "bg-secondary" };
  if (score >= 145) return { label: "Passing",       text: "text-success",   badge: "bg-success-container text-success", bar: "bg-success" };
  return { label: "Not Yet Passing", text: "text-error", badge: "bg-error-container text-error", bar: "bg-error" };
}
function trendIcon(t) {
  if (t === "up")   return '<span class="material-symbols-outlined text-success text-[18px] icon-fill">trending_up</span>';
  if (t === "down") return '<span class="material-symbols-outlined text-error text-[18px] icon-fill">trending_down</span>';
  return '<span class="material-symbols-outlined text-on-surface-variant text-[18px]">trending_flat</span>';
}
function avg(nums) { return nums.reduce((a, b) => a + b, 0) / nums.length; }

/* ---------- track toggle UI ---------- */
function mountTrackToggle(el) {
  if (!el) return;
  function render() {
    const cur = getTrackId();
    el.innerHTML = `
      <div class="inline-flex bg-surface-container rounded-full p-[3px] border border-outline-variant/30 shadow-sm">
        ${Object.values(SCHOLASTICA.tracks).map(t => `
          <button data-track="${t.id}" class="px-md py-xs rounded-full font-label-md text-label-md transition-all ${
            t.id === cur ? "bg-primary text-on-primary shadow-sm" : "text-on-surface-variant hover:text-primary"
          }">${t.label}</button>`).join("")}
      </div>`;
    el.querySelectorAll("button[data-track]").forEach(b =>
      b.addEventListener("click", () => { setTrack(b.dataset.track); render(); }));
  }
  render();
}

/* keep the header avatar initials in sync if present */
document.addEventListener("trackchange", () => {
  document.querySelectorAll("[data-avatar-initials]").forEach(n => n.textContent = getTrack().student.initials);
});

/* ---------- e-library (Calibre-web) ---------- */
// Default calibre-web base URL for the school. Leave "" to let each device set it
// in the E-Library page, or hard-code the school's server here, e.g. "http://library.school.local:8083".
SCHOLASTICA.libraryUrlDefault = "";
const LIB_KEY = "scholastica-library-url";
function getLibraryUrl() { return (localStorage.getItem(LIB_KEY) || SCHOLASTICA.libraryUrlDefault || "").replace(/\/+$/, ""); }
function setLibraryUrl(u) { localStorage.setItem(LIB_KEY, (u || "").trim().replace(/\/+$/, "")); }
