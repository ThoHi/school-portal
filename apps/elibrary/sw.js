const CACHE = 'scholastica-elibrary-v1';
const PAGES = [
  'index.html',
  'login.html',
  'app.js',
  'auth.js',
  'notify.js',
  'manifest.json',
  'icon.svg'
];

self.addEventListener('install', e => {
  e.waitUntil(caches.open(CACHE).then(c => c.addAll(PAGES)));
  self.skipWaiting();
});

self.addEventListener('activate', e => {
  e.waitUntil(
    caches.keys().then(keys =>
      Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k)))
    )
  );
  self.clients.claim();
});

self.addEventListener('fetch', e => {
  if (e.request.method !== 'GET') return;
  e.respondWith(
    caches.match(e.request).then(cached => cached || fetch(e.request).then(res => {
      const clone = res.clone();
      caches.open(CACHE).then(c => c.put(e.request, clone));
      return res;
    }))
  );
});

// Focus (or open) the app when a notification is clicked.
self.addEventListener('notificationclick', e => {
  e.notification.close();
  e.waitUntil(
    self.clients.matchAll({ type: 'window', includeUncontrolled: true }).then(list => {
      for (const c of list) { if ('focus' in c) return c.focus(); }
      if (self.clients.openWindow) return self.clients.openWindow('index.html');
    })
  );
});
