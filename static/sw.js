// sw.js（完成版：ステップ1 / 安全なキャッシュ更新対応）
const CACHE_NAME = "hinan-v6"; // 変更したら v3, v4... と上げる
const PRECACHE_URLS = ["/places/"];

function isPlaces(url) {
  return url.pathname === "/places/";
}

function isCategoryOnly(url) {
  if (!isPlaces(url)) return false;
  const sp = url.searchParams;

  const category = sp.get("category");
  const q = sp.get("q"); // 空文字もあり得る

  // category は必須
  if (!category) return false;

  // q が「存在しても空」ならOK。何か入ってたらNG
  if (q && q.trim() !== "") return false;

  // それ以外の余計なパラメータがあったらNG（必要なら増やせる）
  const allowedKeys = new Set(["category", "q"]);
  const onlyAllowed = [...sp.keys()].every((k) => allowedKeys.has(k));
  return onlyAllowed;
}

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
      (async () => {
        try {
          const res = await fetch(req);

          // キャッシュ方針：
          // - /places/ はキャッシュする
          // - /places/?category=...（カテゴリだけ）もキャッシュする（オフラインでカテゴリ検索できるように）
          // - それ以外のクエリ付き（キーワード等）はキャッシュしない（貼り付き防止）
          if (isPlaces(url) && (!url.search || isCategoryOnly(url))) {
            const cache = await caches.open(CACHE_NAME);
            await cache.put(url.pathname + url.search, res.clone());
          }

          return res;
        } catch (e) {
          const cache = await caches.open(CACHE_NAME);
          // オフライン時：
          // - リクエストがカテゴリだけなら、そのURLのキャッシュを返す
          // - それ以外は /places/（クエリなし）へ戻す
          if (isCategoryOnly(url)) {
            const cachedCategory = await cache.match(url.pathname + url.search);
            if (cachedCategory) return cachedCategory;
          }
          const cachedPlaces = await cache.match("/places/");
          if (cachedPlaces) return cachedPlaces;

          return new Response("オフラインです。一度オンラインで /places/ を開いてください。", {
            status: 503,
            headers: { "Content-Type": "text/plain; charset=utf-8" },
          });
        }
      })()
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
