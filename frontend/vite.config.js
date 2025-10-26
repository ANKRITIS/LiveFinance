import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    host: true, // This enables listening on 0.0.0.0
    port: 5173, 
    watch: {
      usePolling: true // Optional: Fixes hot reload issues on Windows/Docker sometimes
    }
  }
})