import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

const apiPort = process.env.API_PORT || "8001";
const devPort = process.env.REPL_ID ? 5000 : 5173;

export default defineConfig({
  plugins: [react()],
  server: {
    port: Number(devPort),
    host: process.env.REPL_ID ? "0.0.0.0" : undefined,
    strictPort: true,
    proxy: {
      "/api": {
        target: `http://127.0.0.1:${apiPort}`,
        changeOrigin: true,
      },
    },
  },
});
