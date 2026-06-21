import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

// https://vite.dev/config/
export default defineConfig({
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
  },
})
