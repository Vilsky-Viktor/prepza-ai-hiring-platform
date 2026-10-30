import AxeBuilder from "@axe-core/playwright";
import { expect, type Page, test } from "@playwright/test";

import { setScheme } from "./helpers/theme";
import { loaded } from "./helpers/waits";

// The signed-out pages checked with axe against WCAG 2.2 AA, light and dark, in a left-to-right
// and a right-to-left language, and the dialogs they open. Motion is reduced so no animation is
// caught halfway.
const PAGES = [
  "/",
  "/pricing",
  "/faq",
  "/contact",
  "/practice",
  "/tests",
  "/guides/hiring-engineers",
  "/accessibility",
  "/trust",
  "/api-docs?tab=mcp",
  "/ar",
  "/he/pricing",
];
// Also checked on a phone, where the layout differs most.
const PHONE_PAGES = ["/", "/pricing"];
const THEMES = ["light", "dark"] as const;
const WCAG_AA = ["wcag2a", "wcag2aa", "wcag21a", "wcag21aa", "wcag22aa"];

// Known issues: found by the scan, tracked here until fixed, rather than turning their rules off.
// Each names the rule, the element (a part of its HTML) and why it waits.
const KNOWN_ISSUES: { rule: string; html: RegExp; why: string }[] = [];

/** What axe finds on the page as it is now, but the known issues: each rule broken, with its
 * elements (their HTML, as an id alone, Base UI's generated ones, says nothing) and why. */
async function violations(page: Page) {
  const results = await new AxeBuilder({ page }).withTags(WCAG_AA).analyze();

  return results.violations
    .map((violation) => ({
      rule: violation.id,
      nodes: violation.nodes
        .filter(
          (node) =>
            !KNOWN_ISSUES.some((known) => known.rule === violation.id && known.html.test(node.html)),
        )
        .map((node) => `${node.html.slice(0, 200)}: ${node.failureSummary}`),
    }))
    .filter((violation) => violation.nodes.length > 0);
}

for (const path of PAGES) {
  for (const theme of THEMES) {
    const tag = PHONE_PAGES.includes(path) ? "@phone" : [];

    test(`${path} in ${theme} meets WCAG 2.2 AA`, { tag }, async ({ page }) => {
      await setScheme(page, theme);
      await page.emulateMedia({ reducedMotion: "reduce" });
      await page.goto(path);
      await loaded(page);

      expect(await violations(page)).toEqual([]);
    });
  }
}

// States beyond a page's first look: the sign-in dialog and Mira's panel open, light and dark.
for (const theme of THEMES) {
  test(`the sign-in dialog and the assistant's panel in ${theme} meet WCAG 2.2 AA`, async ({
    page,
  }) => {
    await setScheme(page, theme);
    await page.emulateMedia({ reducedMotion: "reduce" });
    await page.goto("/");
    await loaded(page);

    for (const opener of [
      page.getByRole("banner").getByTestId("header-sign-in"),
      page.getByRole("banner").locator("[data-assistant-toggle]"),
    ]) {
      await opener.click();
      await expect(page.getByRole("dialog")).toBeVisible();
      expect(await violations(page)).toEqual([]);
      await page.keyboard.press("Escape");
      await expect(page.getByRole("dialog")).toHaveCount(0);
    }
  });
}
