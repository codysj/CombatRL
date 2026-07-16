import { defineConfig, devices } from "@playwright/test";

export default defineConfig({
  testDir: "./e2e",
  outputDir: "test-results",
  timeout: 20_000,
  workers: 1,
  reporter: [["list"], ["html", { open: "never" }]],
  use: {
    baseURL: "http://127.0.0.1:4173",
    screenshot: "only-on-failure",
    trace: "off",
  },
  webServer: {
    command: "corepack yarn vite --host 127.0.0.1 --port 4173",
    url: "http://127.0.0.1:4173",
    reuseExistingServer: true,
    timeout: 30_000,
  },
  projects: [
    {
      name: "desktop-edge",
      use: {
        ...devices["Desktop Chrome"],
        channel: "msedge",
        launchOptions: { args: ["--disable-gpu", "--use-angle=swiftshader"] },
      },
    },
  ],
});
