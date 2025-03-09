/** @type {import('next').NextConfig} */
const nextConfig = {
  // 禁用静态页面生成
  output: 'standalone',
  // 禁用数据缓存
  experimental: {
    // 禁用React服务器组件缓存
    serverComponentsExternalPackages: [],
    // 禁用数据缓存
    serverActions: {
      bodySizeLimit: '2mb'
    }
  },
  // 配置缓存策略
  headers: async () => [
    {
      source: '/:path*',
      headers: [
        {
          key: 'Cache-Control',
          value: 'no-store, must-revalidate'
        },
        {
          key: 'Pragma',
          value: 'no-cache'
        },
        {
          key: 'Expires',
          value: '0'
        }
      ]
    }
  ]
};

module.exports = nextConfig;