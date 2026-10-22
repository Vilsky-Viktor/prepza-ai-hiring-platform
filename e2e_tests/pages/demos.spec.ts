import { expect, test } from "@playwright/test";

import { loaded } from "./helpers/waits";

const DEMOS = "https://www.youtube.com/@prepza";

// The home page's closing screen links to prepza's demo videos on YouTube, in a new tab, with a
// tooltip on hover.
test("the home page links to the demo videos", async ({ page }) => {
  test.setTimeout(120_000);
  await page.goto("/");
  const demos = page.locator(`main a[href="${DEMOS}"]`);
  await expect(demos).toHaveCount(1);
  await expect(demos).toHaveAttribute("target", "_blank");
  await expect(demos).toHaveAttribute("rel", /noopener/);
  await demos.scrollIntoViewIfNeeded();

  // Hovering opens its tooltip (again if the first hover came before the page was ready).
  await expect(async () => {
    await page.mouse.move(0, 0);
    await demos.hover();
    await expect(demos).toHaveAttribute("data-popup-open", {
      timeout: 2_000,
    });
  }).toPass();
});

// Every page's footer has "ask Mira" under the social icons; it opens the assistant's panel.
test("the footer's ask Mira opens the assistant", async ({ page }) => {
  await page.goto("/faq");
  await loaded(page);
  await page.getByRole("contentinfo").locator("[data-assistant-toggle]").click();
  await expect(page.getByRole("dialog")).toBeVisible();
});
