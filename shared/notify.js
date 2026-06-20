/* Scholastica Portal — local notifications.

   This static PWA has no backend, so it can't do true server-pushed Web Push
   (that needs a server with VAPID keys). Instead it uses the browser
   Notification API + the service worker to show LOCAL notifications:
     - a one-tap "Enable notifications" flow + test notification
     - "new grade posted" alerts fired when a teacher saves a grade
     - a bell popover listing upcoming items for the current track

   To upgrade to real push later, add a backend, generate VAPID keys, call
   registration.pushManager.subscribe(), and POST the subscription to it. */
(function () {
  "use strict";

  const supported = "Notification" in window;

  function permission() { return supported ? Notification.permission : "unsupported"; }

  async function show(title, opts) {
    if (!supported || Notification.permission !== "granted") return false;
    opts = Object.assign({ icon: "icon.svg", badge: "icon.svg" }, opts || {});
    try {
      if ("serviceWorker" in navigator) {
        const reg = await navigator.serviceWorker.ready;
        await reg.showNotification(title, opts);
        return true;
      }
    } catch (_) { /* fall back to page notification */ }
    new Notification(title, opts);
    return true;
  }

  async function enable() {
    if (!supported) return "unsupported";
    let p = Notification.permission;
    if (p === "default") p = await Notification.requestPermission();
    if (p === "granted") {
      show("Notifications on", { body: "You'll get alerts for new grades and reminders." });
    }
    document.dispatchEvent(new CustomEvent("notifystatechange", { detail: { permission: p } }));
    return p;
  }

  // Called by the grades page when a teacher saves a score.
  function gradePosted(subjectName, scoreText, studentName) {
    return show("New grade posted", {
      body: `${subjectName}: ${scoreText}` + (studentName ? ` · ${studentName}` : ""),
      tag: "grade-" + subjectName,
    });
  }

  // ---- Bell popover (auto-wired to the header notifications button) ----
  function upcomingItems() {
    try { return (typeof getTrack === "function" ? getTrack().upcoming : []) || []; }
    catch (_) { return []; }
  }

  function buildPopover() {
    const pop = document.createElement("div");
    pop.id = "notify-popover";
    pop.className = "hidden fixed right-2 top-16 z-50 w-80 max-w-[calc(100vw-1rem)] bg-surface-container-lowest border border-outline-variant/40 rounded-xl shadow-lg overflow-hidden";
    document.body.appendChild(pop);
    return pop;
  }

  function renderPopover(pop) {
    const perm = permission();
    const items = upcomingItems();
    const enableRow = perm === "granted"
      ? `<span class="inline-flex items-center gap-xs font-body-sm text-body-sm text-success"><span class="material-symbols-outlined text-[16px] icon-fill">check_circle</span> Notifications on</span>
         <button id="notify-test" class="font-label-md text-label-md text-primary hover:underline">Send test</button>`
      : perm === "unsupported"
        ? `<span class="font-body-sm text-body-sm text-on-surface-variant">Not supported on this browser.</span>`
        : `<button id="notify-enable" class="bg-primary text-on-primary px-sm py-xs rounded-lg font-label-md text-label-md hover:opacity-90 transition-opacity">Enable notifications</button>`;

    pop.innerHTML = `
      <div class="flex items-center justify-between p-sm border-b border-outline-variant/20">
        <span class="font-label-md text-label-md text-primary">Notifications</span>
        <button id="notify-close" class="p-1 text-on-surface-variant hover:text-primary"><span class="material-symbols-outlined text-[18px]">close</span></button>
      </div>
      <div class="flex items-center justify-between gap-sm p-sm border-b border-outline-variant/20">${enableRow}</div>
      <div class="p-sm">
        <span class="block font-label-md text-label-md text-on-surface-variant uppercase tracking-wider text-[10px] mb-xs">Upcoming</span>
        ${items.length ? items.map(u => `
          <div class="flex items-center gap-sm py-xs">
            <span class="material-symbols-outlined text-secondary text-[20px] shrink-0">${u.icon || "event"}</span>
            <div class="min-w-0">
              <span class="block font-body-sm text-body-sm text-on-surface truncate">${u.subject}</span>
              <span class="block font-body-sm text-[12px] text-on-surface-variant">${u.when}</span>
            </div>
          </div>`).join("")
          : `<span class="font-body-sm text-body-sm text-on-surface-variant">Nothing upcoming.</span>`}
      </div>`;

    const close = () => pop.classList.add("hidden");
    pop.querySelector("#notify-close").addEventListener("click", close);
    const enableBtn = pop.querySelector("#notify-enable");
    if (enableBtn) enableBtn.addEventListener("click", async () => { await enable(); renderPopover(pop); });
    const testBtn = pop.querySelector("#notify-test");
    if (testBtn) testBtn.addEventListener("click", () => show("Test notification", { body: "This is how alerts will appear." }));
  }

  function wireBell() {
    // Find header bell button(s): a <button> containing the "notifications" icon.
    const bells = Array.prototype.filter.call(document.querySelectorAll("button"), b =>
      /notifications/.test(b.textContent || "") && b.querySelector(".material-symbols-outlined"));
    if (!bells.length) return;
    const pop = buildPopover();

    bells.forEach(bell => {
      // Hide the static red dot until there's something to show.
      const dot = bell.querySelector("span.absolute");
      if (dot) dot.style.display = upcomingItems().length ? "" : "none";
      bell.addEventListener("click", e => {
        e.preventDefault();
        if (pop.classList.contains("hidden")) { renderPopover(pop); pop.classList.remove("hidden"); }
        else pop.classList.add("hidden");
      });
    });

    // Close on outside click.
    document.addEventListener("click", e => {
      if (pop.classList.contains("hidden")) return;
      if (!pop.contains(e.target) && !bells.some(b => b.contains(e.target))) pop.classList.add("hidden");
    });
    document.addEventListener("datachange", () => { if (!pop.classList.contains("hidden")) renderPopover(pop); });
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", wireBell);
  else wireBell();

  window.Notify = { permission, enable, show, gradePosted };
})();
