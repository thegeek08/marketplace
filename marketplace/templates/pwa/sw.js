{% load static %}
/* ============================================================
   Service Worker — Marketplace Sénégal
   Stratégie :
     - Install  : pré-cache offline page + assets critiques
     - Activate : purge des anciens caches
     - Fetch    : Network First pour HTML, Cache First pour assets
   ============================================================ */

const CACHE_VERSION = 'v1';
const CACHE_STATIC  = 'marketplace-static-'  + CACHE_VERSION;
const CACHE_DYNAMIC = 'marketplace-dynamic-' + CACHE_VERSION;

const PRECACHE_URLS = [
  '/offline/',
  '/static/manifest.json',
  '/static/icons/icon-192.png',
  '/static/icons/icon-512.png',
  /* Bootstrap (CDN) */
  'https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css',
  'https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js',
];

/* ── INSTALL : pré-chargement du cache ── */
self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_STATIC).then(cache => {
      return cache.addAll(PRECACHE_URLS);
    })
  );
  self.skipWaiting();
});

/* ── ACTIVATE : nettoyage des anciens caches ── */
self.addEventListener('activate', event => {
  const CURRENT = [CACHE_STATIC, CACHE_DYNAMIC];
  event.waitUntil(
    caches.keys().then(keys =>
      Promise.all(
        keys
          .filter(key => !CURRENT.includes(key))
          .map(key => caches.delete(key))
      )
    )
  );
  self.clients.claim();
});

/* ── FETCH ── */
self.addEventListener('fetch', event => {
  const { request } = event;
  const url = new URL(request.url);

  /* Ignorer les requêtes non-GET et les URLs d'admin/API */
  if (request.method !== 'GET') return;
  if (url.pathname.startsWith('/admin/')) return;

  /* Assets statiques → Cache First */
  if (
    url.pathname.startsWith('/static/') ||
    url.hostname === 'cdn.jsdelivr.net'
  ) {
    event.respondWith(cacheFirst(request));
    return;
  }

  /* Pages HTML → Network First avec fallback offline */
  if (request.headers.get('Accept') && request.headers.get('Accept').includes('text/html')) {
    event.respondWith(networkFirstWithOfflineFallback(request));
    return;
  }

  /* Tout le reste → Network First */
  event.respondWith(networkFirst(request));
});

/* ── Stratégies ── */

async function cacheFirst(request) {
  const cached = await caches.match(request);
  if (cached) return cached;
  try {
    const response = await fetch(request);
    if (response.ok) {
      const cache = await caches.open(CACHE_STATIC);
      cache.put(request, response.clone());
    }
    return response;
  } catch {
    return new Response('', { status: 408 });
  }
}

async function networkFirst(request) {
  try {
    const response = await fetch(request);
    if (response.ok) {
      const cache = await caches.open(CACHE_DYNAMIC);
      cache.put(request, response.clone());
    }
    return response;
  } catch {
    const cached = await caches.match(request);
    return cached || new Response('', { status: 408 });
  }
}

async function networkFirstWithOfflineFallback(request) {
  try {
    const response = await fetch(request);
    if (response.ok) {
      const cache = await caches.open(CACHE_DYNAMIC);
      cache.put(request, response.clone());
    }
    return response;
  } catch {
    const cached = await caches.match(request);
    if (cached) return cached;
    /* Fallback vers la page offline */
    return caches.match('/offline/');
  }
}
