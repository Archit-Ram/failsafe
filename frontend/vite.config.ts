import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/api": {
        // Override with VITE_API_PROXY env var if your backend runs elsewhere.
        target: process.env.VITE_API_PROXY ?? "http://localhost:8765",
        changeOrigin: true,
      },
    },
  },
});
