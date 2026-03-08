import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    host: true,   // binds to both 0.0.0.0 (IPv4) and :: (IPv6)
    port: 5173,
    strictPort: true,
  }
})


