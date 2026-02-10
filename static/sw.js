const CACHE_NAME = "hinan-v1";
const PRECACHE_URLS = [
  "/places/"
];

// インストール時：最低限の入口だけキャッシュ
self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => cache.addAll(PRECACHE_URLS))
  );
  self.skipWaiting();
});

// 有効化：即時反映
self.addEventListener("activate", (event) => {
  event.waitUntil(self.clients.claim());
});

// 取得戦略
self.addEventListener("fetch", (event) => {
  const req = event.request;
  const url = new URL(req.url);

  // 同一オリジンだけ対象
  if (url.origin !== location.origin) return;

  // ページ遷移（HTML）はネット優先
  if (req.mode === "navigate") {
    event.respondWith(
      fetch(req)
        .then((res) => {
          const copy = res.clone();
          caches.open(CACHE_NAME).then((cache) => cache.put(req, copy));
          return res;
        })
        .catch(() =>
          caches.match(req).then((cached) => cached || caches.match("/places/"))
        )
    );
    return;
  }

  // 静的ファイルはキャッシュ優先
  event.respondWith(
    caches.match(req).then((cached) => {
      if (cached) return cached;
      return fetch(req).then((res) => {
        const copy = res.clone();
        caches.open(CACHE_NAME).then((cache) => cache.put(req, copy));
        return res;
      });
    })
  );
});