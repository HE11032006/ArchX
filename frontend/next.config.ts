import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Produces a minimal self-contained server (.next/standalone) for the
  // single-container deployment — does not affect the Vercel deployment,
  // which uses its own build pipeline regardless of this setting.
  output: "standalone",

  // Proxies /api/* to the FastAPI backend running in the SAME container
  // (127.0.0.1:8000, never exposed outside the container). Combined with
  // NEXT_PUBLIC_API_URL="" at build time (see Dockerfile), this makes
  // shared/api/client.ts issue relative fetches that land here — no CORS,
  // no public tunnel URL to keep in sync on every restart.
  //
  // Inert on Vercel: there, NEXT_PUBLIC_API_URL is set to the real tunnel
  // URL, so apiFetch calls that absolute URL directly and this rewrite is
  // never reached.
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: "http://127.0.0.1:8000/api/:path*",
      },
    ];
  },
};

export default nextConfig;
