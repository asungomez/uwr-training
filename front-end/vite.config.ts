import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

// https://vite.dev/config/
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')
  // Where the dev proxy forwards /api. `api:8000` inside Docker, localhost on host.
  const apiTarget = env['API_PROXY_TARGET'] ?? 'http://localhost:8000'

  return {
    plugins: [react(), tailwindcss()],
    server: {
      // Listen on all interfaces so the dev server is reachable from outside the container.
      host: true,
      port: 5173,
      watch: {
        // Bind-mounted volumes on macOS/Windows don't reliably emit fs events,
        // so poll to keep hot-reload working.
        usePolling: true,
      },
      proxy: {
        // Same-origin API calls: forward /api/* to the back-end, stripping /api
        // since the API serves its routes at the root.
        '/api': {
          target: apiTarget,
          changeOrigin: true,
          rewrite: (path) => path.replace(/^\/api/, ''),
        },
      },
    },
  }
})
