/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  swcMinify: true,
  webpack: (config) => {
    // Handle canvas binary module
    config.resolve.alias = {
      ...config.resolve.alias,
      canvas: false,
    };
    return config;
  },
  // Disable image optimization for static export
  images: {
    unoptimized: true,
  },
}

module.exports = nextConfig
