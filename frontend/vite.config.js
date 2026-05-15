import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    strictPort: true,
    proxy: {
      "/api": {
        // Dev API default port (see scripts/start-api.ps1). Use 8001 when port 8000 has a stale listener.
        target: "http://127.0.0.1:8001",
        changeOrigin: true,
      },
    },
  },
});
