/** @type {import('next').NextConfig} */
const API_BASE = process.env.OPENCS_API_BASE ?? "http://opencs-api:8000";

const config = {
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
