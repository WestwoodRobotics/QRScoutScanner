const CACHE_NAME = 'qrscout-cache-v1';
const urlsToCache = [
  '/',
  '/index.html',
  '/static/main.css',
  '/static/qr-scanner.js',
  '/static/Octocat.png'
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then((cache) => cache.addAll(urlsToCache))
      .then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then(cacheNames => {
      return Promise.all(
        cacheNames.map(cacheName => {
          if (cacheName !== CACHE_NAME) {
            return caches.delete(cacheName);
          }
        })
      );
    })
  );
});

self.addEventListener('fetch', (event) => {
  // For navigation requests, always return cached index.html
  if (event.request.mode === 'navigate') {
    event.respondWith(
      caches.match('/index.html')
    );
    return;
  }
  // For other requests, try cache first, then network as fallback
  event.respondWith(
    caches.match(event.request).then((response) => {
      return response || fetch(event.request).catch(() => {
        // Optionally, return a fallback for failed requests
      });
    })
  );
});
