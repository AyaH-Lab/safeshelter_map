// sw.js（完成版：ステップ1 / 安全なキャッシュ更新対応）
const CACHE_NAME = "hinan-v2"; // 変更したら v3, v4... と上げる
const PRECACHE_URLS = ["/places/"];

// インストール時：最低限の入口だけキャッシュ
self.addEventListener("install", (event) => {
  event.waitUntil(
    (async () => {
      const cache = await caches.open(CACHE_NAME);
      await cache.addAll(PRECACHE_URLS);
    })()
  );
  self.skipWaiting();
});

// 有効化：古いキャッシュ削除 → 即時反映
self.addEventListener("activate", (event) => {
  event.waitUntil(
    (async () => {
      const keys = await caches.keys();
      await Promise.all(keys.filter((k) => k !== CACHE_NAME).map((k) => caches.delete(k)));
      await self.clients.claim();
    })()
  );
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
          // オンライン時：開いたページをキャッシュ（将来の閲覧用）
          const copy = res.clone();
          caches.open(CACHE_NAME).then((cache) => cache.put(req, copy));
          return res;
        })
        .catch(async () => {
          // ステップ1方針：
          // オフライン時は検索・絞り込み結果を保証しない → 常に一覧へ戻す
          const cached = await caches.match("/places/", { ignoreSearch: true });
          if (cached) return cached;

          // もしキャッシュが無い場合の最終保険
          return new Response("オフラインです。一度オンラインで /places/ を開いてください。", {
            status: 503,
            headers: { "Content-Type": "text/plain; charset=utf-8" },
          });
        })
    );
    return;
  }

  // 静的ファイルはキャッシュ優先（無ければネット→保存）
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
