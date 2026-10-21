import { REQUEST_URL } from "./env";

// Every kind of page the specs open; a made-up address still compiles its route.
const WARM_UP_PATHS = [
  "/",
  "/companies",
  "/pricing",
  "/terms",
  "/privacy",
  "/documents",
  "/faq",
  "/about",
  "/contact",
  "/accessibility",
  "/practice",
  "/practice/e2e-warm-up",
  "/tests",
  "/tests/e2e-warm-up",
  "/compare",
  "/compare/testgorilla",
  "/guides",
  "/guides/hiring-engineers",
  "/pre-employment-testing",
  "/ai-interviews",
  "/api-docs",
  "/connect",
  "/news",
  "/news/rss.xml",
  "/sitemap.xml",
  "/unsubscribe",
  "/invite/e2e-warm-up",
  "/de",
  "/de/pricing",
];
// Long enough for a cold dev server to compile a page, or to come back from a restart.
const PAGE_DEADLINE_MS = 120_000;

/** The local frontend is a dev server that compiles each page on its first visit; asking for
 * every page once before the browsers start keeps those compiles out of the tests' time. */
export async function warmUp() {
  for (const path of WARM_UP_PATHS) {
    const deadline = Date.now() + PAGE_DEADLINE_MS;

    while (Date.now() < deadline) {
      const status = await fetch(`${REQUEST_URL}${path}`, { redirect: "manual" })
        .then((response) => response.status)
        .catch(() => 0);

      // A 502 or no answer: the dev server is restarting.
      if (status > 0 && status !== 502) {
        break;
      }

      await new Promise((resolve) => setTimeout(resolve, 2_000));
    }
  }
}
