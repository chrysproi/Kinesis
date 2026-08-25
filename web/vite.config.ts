import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";

export default defineConfig({
  plugins: [react(), tailwindcss()],
  base: "/Kinesis/",

  // MapLibre loads its worker as a separate module. Pre-bundling rewrites
  // the path and the worker 404s, leaving a blank canvas with no error.
  optimizeDeps: { exclude: ["maplibre-gl"] },
});
