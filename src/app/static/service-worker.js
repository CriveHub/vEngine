
// Precaching assets
const CACHE_NAME = 'engineproject-cache-v1';
const PRECACHE_URLS = [
  '/',
  '/dashboard.html',
  '/static/bundle.js'
];
self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME).then(cache => cache.addAll(PRECACHE_URLS))
  );
});
// Service Worker stub
self.addEventListener('install', event => event.skipWaiting());

// Runtime caching for API
self.addEventListener('fetch', event => {
  if (event.request.url.includes('/api/')) {
    event.respondWith(
      caches.open(CACHE_NAME).then(cache => {
        return cache.match(event.request).then(resp => {
          return resp || fetch(event.request).then(response => {
            cache.put(event.request, response.clone());
            return response;
          });
        });
      })
    );
  }
});
