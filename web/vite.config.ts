import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";

export default defineConfig({
  plugins: [react(), tailwindcss()],
  // Set to "/<repo-name>/" when deploying to a GitHub Pages project site
  base: "/",

  // MapLibre loads its worker as a separate module. Pre-bundling rewrites
  // the path and the worker 404s, leaving a blank canvas with no error.
  optimizeDeps: { exclude: ["maplibre-gl"] },
});
