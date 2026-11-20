import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// 开发环境把 /api 与 /ws 代理到 gateway——web-ui 只经网关访问，不直连求解库。
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/api": { target: "http://localhost:3001", changeOrigin: true },
      "/ws": { target: "ws://localhost:3001", ws: true },
    },
  },
  build: { outDir: "dist" },
});
