import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  reactStrictMode: true,
  output: "standalone",
  // Keep the standalone layout flat (server.js at the root): the Docker image runs `node server.js`.
  outputFileTracingRoot: __dirname,
  async rewrites() {
    // In production Caddy routes /api/* straight to the API; this rewrite serves local dev and any direct hits.
    return [{ source: "/api/:path*", destination: `${process.env.API_ORIGIN ?? "http://localhost:8000"}/api/:path*` }];
  },
};

export default nextConfig;
