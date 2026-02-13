import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

// 获取API代理目标地址 - Docker环境使用backend服务名，本地开发使用localhost
const API_TARGET = process.env.VITE_API_TARGET || 'http://localhost:8000'

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: 5173,
    host: true,
    proxy: {
      '/api': {
        target: API_TARGET,
        changeOrigin: true,
      },
    },
  },
})
