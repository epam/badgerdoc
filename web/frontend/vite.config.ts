import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import { tanstackRouter } from '@tanstack/router-plugin/vite'
import path from 'path'
import { hocrTextPlugin } from './hocrTextPlugin'

export default defineConfig(({ command }) => ({
  base: command === 'build' ? '/static/badgerdoc-frontend/' : '/',
  plugins: [hocrTextPlugin(), tanstackRouter(), react(), tailwindcss()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  define: {
    __STATIC_ASSETS__: command === 'build' ? '"/static/badgerdoc-frontend"' : '"../../public"',
  },
  server: {
    proxy: {
      // Proxy BadgerDoc API requests to bypass CORS
      '/badgerdoc': {
        target: 'http://localhost',
        changeOrigin: true,
        // No rewrite needed - path stays as /badgerdoc/...
        configure: (proxy) => {
          // Remove Origin header to prevent CSRF origin checking issues
          proxy.on('proxyReq', (proxyReq) => {
            proxyReq.removeHeader('origin')
          })
        },
      },
    },
  },
}))
