import { defineConfig, devices } from "@playwright/test"

// Runs in Playwright's Docker image (e2e_tests/pages.sh). The browser keeps the site's own
// address, so Next.js sees its usual origin; HOST_RULES points it at the gateway on the compose
// network.
export default defineConfig({
  testDir: ".",
  reporter: "list",
  // A test.only left in fails the run instead of quietly skipping every other test.
  forbidOnly: true,
  use: {
    baseURL: process.env.SITE_URL ?? "http://localhost:8090",
    // What happened in a failed test, step by step: npx playwright show-trace <trace.zip>.
    trace: "retain-on-failure",
    launchOptions: {
      args: process.env.HOST_RULES
        ? [`--host-resolver-rules=${process.env.HOST_RULES}`]
        : [],
    },
  },
  projects: [
    {
      name: "desktop",
      use: { ...devices["Desktop Chrome"], viewport: { width: 1280, height: 800 } },
    },
    { name: "phone", use: { ...devices["Pixel 7"] } },
  ],
})
