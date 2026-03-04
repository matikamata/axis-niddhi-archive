/**
 * 💎 BRASILEIRINHO ENGINE — AXIS-NIDDHI v3.0
 * sw.js — Service Worker (offline cache)
 *
 * BUILD_ID é substituído pelo build.py antes de copiar para o output.
 * Ativação: descomentar o bloco em base.html.
 */

const BUILD_ID    = '78f82c9a205578d2';
const CACHE_NAME  = 'brasileirinho-' + BUILD_ID;
const OFFLINE_URL = 'index.html';

/* Assets para pré-cache */
const PRECACHE_ASSETS = [
  './',
  './index.html',
  './css/style.css',
  './js/main.js',
  './js/reading-flow.js',
  './search_index.json',
  './index.json',
];

self.addEventListener('install', function (event) {
  event.waitUntil(
    caches.open(CACHE_NAME).then(function (cache) {
      return cache.addAll(PRECACHE_ASSETS);
    }).then(function () {
      return self.skipWaiting();
    })
  );
});

self.addEventListener('activate', function (event) {
  event.waitUntil(
    caches.keys().then(function (keys) {
      return Promise.all(
        keys.filter(function (k) { return k !== CACHE_NAME; })
            .map(function (k) { return caches.delete(k); })
      );
    }).then(function () {
      return self.clients.claim();
    })
  );
});

self.addEventListener('fetch', function (event) {
  if (event.request.method !== 'GET') return;

  event.respondWith(
    caches.match(event.request).then(function (cached) {
      if (cached) return cached;
      return fetch(event.request).then(function (response) {
        if (!response || response.status !== 200 || response.type !== 'basic') {
          return response;
        }
        const clone = response.clone();
        caches.open(CACHE_NAME).then(function (cache) {
          cache.put(event.request, clone);
        });
        return response;
      }).catch(function () {
        // Offline fallback
        return caches.match(OFFLINE_URL);
      });
    })
  );
});
