import type { NextConfig } from "next";

const API_BASE = process.env.OPENCS_API_BASE ?? "http://opencs-api:8000";

const config: NextConfig = {
  async rewrites() {
    return [
      {
        source: "/api/admin/:path*",
        destination: `${API_BASE}/admin/:path*`,
      },
    ];
  },
  output: "standalone",
};

export default config;
