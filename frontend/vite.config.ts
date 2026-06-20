import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  build: {
    // Three.js is isolated behind React.lazy; keep its minified renderer chunk within this budget.
    chunkSizeWarningLimit: 560,
  },
  test: {
    environment: "node",
  },
});
