import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { fileURLToPath, URL } from "node:url";

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@": fileURLToPath(new URL("./src", import.meta.url)),
    },
    // Guarantee a single React instance (avoids "Invalid hook call").
    dedupe: ["react", "react-dom"],
  },
  server: {
    port: 3000,
  },
});
