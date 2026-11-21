import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// In dev, /api is proxied to the gateway. In production set VITE_API_URL (or use the nginx proxy in Docker).
export default defineConfig({
  plugins: [react()],
  server: { port: 3000, proxy: { "/api": "http://localhost:8000" } },
});
