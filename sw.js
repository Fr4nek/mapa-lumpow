const CACHE_NAME = 'map-pwa-v1';

// Instalacja i czyszczenie starych cache
self.addEventListener('install', (e) => {
    self.skipWaiting();
});

// Obsługa zapytań (sieć najpierw, bez zaawansowanego offline na start)
self.addEventListener('fetch', (e) => {
    e.respondWith(fetch(e.request));
});