/** @type {import('next').NextConfig} */
const nextConfig = {
  eslint: {
    // ✅ Completely ignore ESLint during build
    ignoreDuringBuilds: true,
  },
  typescript: {
    // ✅ Ignore TypeScript errors during build too
    ignoreBuildErrors: true,
  },
  output: 'standalone',
  // Optional: Add other Next.js config here
}

export default nextConfig