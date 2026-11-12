/**
 * Kuyumbank SW
 * - index.html / navigasyon: network-first (stale UI yok)
 * - /assets/* (Vite hash’li): cache-first
 * - /api/*: network only
 * CACHE_NAME sürümle; deploy’da artır.
 */
const CACHE_VERSION = "v3";
const CACHE_NAME = `kuyumbank-pwa-${CACHE_VERSION}`;

self.addEventListener("install", (event) => {
  self.skipWaiting();
  event.waitUntil(Promise.resolve());
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches
      .keys()
      .then((keys) =>
        Promise.all(keys.filter((k) => k !== CACHE_NAME).map((k) => caches.delete(k)))
      )
      .then(() => self.clients.claim())
  );
});

function isNavigation(request) {
  return (
    request.mode === "navigate" ||
    (request.method === "GET" &&
      request.headers.get("accept")?.includes("text/html"))
  );
}

function isHashedAsset(url) {
  return (
    url.pathname.startsWith("/assets/") ||
    /-[A-Za-z0-9_-]{6,}\.(js|css|woff2?|png|svg|webp)$/.test(url.pathname)
  );
}

self.addEventListener("fetch", (event) => {
  const { request } = event;
  if (request.method !== "GET") return;

  const url = new URL(request.url);
  if (url.origin !== self.location.origin) return;

  if (url.pathname.startsWith("/api/")) {
    return;
  }

  if (isNavigation(request) || url.pathname === "/" || url.pathname.endsWith(".html")) {
    event.respondWith(
      fetch(request)
        .then((res) => res)
        .catch(() => caches.match("/index.html"))
    );
    return;
  }

  if (isHashedAsset(url)) {
    event.respondWith(
      caches.match(request).then((cached) => {
        if (cached) return cached;
        return fetch(request).then((res) => {
          if (res.ok) {
            const copy = res.clone();
            caches.open(CACHE_NAME).then((cache) => cache.put(request, copy));
          }
          return res;
        });
      })
    );
    return;
  }

  event.respondWith(
    fetch(request)
      .then((res) => {
        if (res.ok) {
          const copy = res.clone();
          caches.open(CACHE_NAME).then((cache) => cache.put(request, copy));
        }
        return res;
      })
      .catch(() => caches.match(request))
  );
});
