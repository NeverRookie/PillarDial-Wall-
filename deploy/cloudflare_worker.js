/**
 * Cloudflare Worker 反向代理与边缘缓存网关
 * 可以将请求路由到自建 VPS / Railway / Render / Fly.io 服务器
 */

const BACKEND_ORIGIN = "https://your-server-domain.com"; // 替换为您的实际后端服务器地址

export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);

    // 构建目标 URL
    const targetUrl = new URL(url.pathname + url.search, BACKEND_ORIGIN);

    // 针对 /generate 请求使用 Cloudflare 边缘缓存
    if (url.pathname === "/generate") {
      const cache = caches.default;
      const cacheKey = new Request(url.toString(), request);
      let response = await cache.match(cacheKey);

      if (!response) {
        response = await fetch(targetUrl.toString(), {
          headers: request.headers,
          method: request.method,
        });

        // 重新包装响应，确保边缘缓存生效 24 小时
        const newHeaders = new Headers(response.headers);
        newHeaders.set("Cache-Control", "public, max-age=86400, s-maxage=86400");
        newHeaders.set("Access-Control-Allow-Origin", "*");

        response = new Response(response.body, {
          status: response.status,
          statusText: response.statusText,
          headers: newHeaders,
        });

        ctx.waitUntil(cache.put(cacheKey, response.clone()));
      }
      return response;
    }

    // 其他请求直接透明转发
    return fetch(targetUrl.toString(), {
      headers: request.headers,
      method: request.method,
    });
  },
};
