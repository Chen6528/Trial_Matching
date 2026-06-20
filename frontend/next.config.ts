import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Pin the workspace root. A stray package-lock.json in a parent directory
  // otherwise makes Turbopack infer the wrong root; this file's directory
  // (frontend/) is the real project root.
  turbopack: {
    root: import.meta.dirname,
  },
};

export default nextConfig;
