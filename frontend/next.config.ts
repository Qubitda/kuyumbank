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
  async rewrites() {
    return [
      {
        source: "/api/v1/:path*",
        destination: `${djangoOrigin}/api/v1/:path*`,
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
