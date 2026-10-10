import type { NextConfig } from 'next';
const backendUrl = (process.env.GREENPRINT_BACKEND_URL || 'http://127.0.0.1:8001').replace(/\/$/, '');
const config: NextConfig = {
  poweredByHeader: false,
  distDir: process.env.GREENPRINT_NEXT_DIST_DIR || '.next',
  async rewrites() {
    return [{ source: '/api/backend/:path*', destination: `${backendUrl}/:path*` }];
  },
};
export default config;
