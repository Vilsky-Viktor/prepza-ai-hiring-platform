import AxeBuilder from "@axe-core/playwright";
import { expect, test } from "@playwright/test";

import { setScheme } from "./helpers/theme";
import { loaded } from "./helpers/waits";

// The signed-out pages checked with axe against WCAG 2.2 AA, light and dark, in a left-to-right
// and a right-to-left language. Motion is reduced so no animation is caught halfway.
const PAGES = [
  "/",
  "/pricing",
  "/faq",
  "/contact",
  "/practice",
  "/tests",
  "/guides/hiring-engineers",
  "/accessibility",
  "/api-docs?tab=mcp",
  "/ar",
  "/he/pricing",
];
const THEMES = ["light", "dark"] as const;
const WCAG_AA = ["wcag2a", "wcag2aa", "wcag21a", "wcag21aa", "wcag22aa"];

for (const path of PAGES) {
  for (const theme of THEMES) {
    test(`${path} in ${theme} meets WCAG 2.2 AA`, async ({ page }) => {
      await setScheme(page, theme);
      await page.emulateMedia({ reducedMotion: "reduce" });
      await page.goto(path);
      await loaded(page);

      const results = await new AxeBuilder({ page }).withTags(WCAG_AA).analyze();
      const found = results.violations.map((violation) => ({
        rule: violation.id,
        // The element itself, as its id alone (Base UI's are generated) says nothing.
        nodes: violation.nodes.map((node) => `${node.html.slice(0, 200)}: ${node.failureSummary}`),
      }));

      expect(found).toEqual([]);
    });
  }
}
