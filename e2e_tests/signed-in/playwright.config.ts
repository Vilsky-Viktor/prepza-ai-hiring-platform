import { defineConfig, devices } from "@playwright/test"

import { SITE_URL } from "./constants"

// Runs in Playwright's Docker image (e2e_tests/signed-in.sh), like the signed-out page tests,
// against the production build of the frontend. HOST_RULES points the site and the Firebase Auth
// emulator at their containers, so the browser keeps the addresses the frontend uses.
// Every test owns its data, so tests run in parallel (WORKERS, default 3: each test's browsers
// keep the laptop's cores busy, and more workers only slow every page down). A test that changes
// something global (maintenance mode, the pause, a limit) is tagged @global: signed-in.sh runs
// those in the `global` project afterwards, one at a time, with nothing else running.
export default defineConfig({
  testDir: "specs",
  // forward.ts maps the local addresses for Firefox and WebKit; clean-before.ts first deletes
  // what stopped runs left (accounts older than teardown.ts's STALE_MS), so no test meets them.
  globalSetup: ["./forward.ts", "./clean-before.ts"],
  // Deletes every throwaway account and its companies after each run (teardown.ts).
  globalTeardown: "./teardown.ts",
  reporter: "list",
  workers: Number(process.env.WORKERS ?? 3),
  // A test.only left in fails the run instead of quietly skipping every other test.
  forbidOnly: true,
  // Once more on failure, so a run finishes; a pass on retry is flaky and gets fixed.
  retries: 1,
  fullyParallel: true,
  timeout: 180_000,
  expect: { timeout: 15_000 },
  use: {
    ...devices["Desktop Chrome"],
    viewport: { width: 1280, height: 800 },
    baseURL: SITE_URL,
    acceptDownloads: true,
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
    launchOptions: {
      args: [
        ...(process.env.HOST_RULES
          ? [`--host-resolver-rules=${process.env.HOST_RULES}`]
          : []),
        // A company's site the tests make up (i-api-embed) embeds the local stack; Chrome would
        // block a public page loading a local one, which never happens with the real site.
        "--disable-features=BlockInsecurePrivateNetworkRequests,PrivateNetworkAccessSendPreflights,LocalNetworkAccessChecks",
      ],
    },
  },
  // Every spec in Chromium (its @global tests in `global`, run on their own by signed-in.sh); the
  // embedded interview also in Firefox and WebKit, where a company's site gets the frame's storage
  // partitioned and no third-party cookies (Playwright starts Chromium with its storage
  // partitioning off); and a candidate's interview in WebKit on an iPhone (`iphone`), as most
  // candidates on iPhones take it in Safari.
  projects: [
    { name: "chromium", grepInvert: /@global/ },
    { name: "global", grep: /@global/, workers: 1 },
    ...(["firefox", "webkit"] as const).map((name) => ({
      name,
      testMatch: /i-api-embed\.spec\.ts/,
      // The embedded interview; the hosted script's headers are a request, the same anywhere.
      grep: /embeds a candidate's interview/,
      use: {
        ...devices[name === "firefox" ? "Desktop Firefox" : "Desktop Safari"],
        viewport: { width: 1280, height: 800 },
        launchOptions: {},
      },
    })),
    {
      name: "iphone",
      testMatch: /b-candidate\.spec\.ts/,
      grep: /candidate takes the interview from the invite link/,
      use: { ...devices["iPhone 15"], launchOptions: {} },
    },
  ],
})
