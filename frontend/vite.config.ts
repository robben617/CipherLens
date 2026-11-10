import { defineConfig, loadEnv } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, '.', '')
  return {
    plugins: [vue()],
    base: env.VITE_BASE || '/',
    server: {
      proxy: {
        '/api': {
          target: 'http://127.0.0.1:8000',
          changeOrigin: true,
        },
      },
    },
    ...(env.VITE_BUILD_TARGET
      ? { build: { target: env.VITE_BUILD_TARGET } }
      : {}),
  }
})
