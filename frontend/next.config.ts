import type { NextConfig } from "next";

/**
 * Aynı-origin reverse proxy (ADR-0017 / CORS erteli).
 * Tarayıcı → /api/v1/* → Next rewrite → Django.
 * Geliştirme: DJANGO_ORIGIN=http://127.0.0.1:8000
 */
const djangoOrigin =
  process.env.DJANGO_ORIGIN?.replace(/\/$/, "") || "http://127.0.0.1:8000";

const nextConfig: NextConfig = {
  cacheComponents: true,
  partialPrefetching: true,
  // Django APPEND_SLASH ister; Next varsayılanı trailing slash'ı 308 ile düşürüp
  // CSRF/login'de 308↔301 döngüsü üretir (NX-FE same-origin rewrite).
  skipTrailingSlashRedirect: true,
  async rewrites() {
    // Django APPEND_SLASH: destination mutlaka trailing slash ile bitsin
    // (Next :path* slash'ı düşürür → 301/308 döngüsü).
    return [
      {
        source: "/api/v1/:path*",
        destination: `${djangoOrigin}/api/v1/:path*/`,
      },
    ];
  },
  turbopack: {
    rules: {
      "*.css": {
        loaders: ["@tailwindcss/turbopack"],
        as: "*.css",
      },
    },
  },
};

export default nextConfig;
