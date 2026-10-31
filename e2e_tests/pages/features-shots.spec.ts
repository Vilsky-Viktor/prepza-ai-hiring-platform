import { expect, test } from "@playwright/test";

import { setScheme } from "./helpers/theme";

// Review pictures of the features page, whole, on a laptop (1440 wide) and a phone (390), light
// and dark: taken only with SHOTS=1; nothing here checks the page (its tests come once the page
// is approved).
test.skip(process.env.SHOTS !== "1", "Review pictures of the features page, with SHOTS=1 only");

const SIZES = [
  { name: "desktop", width: 1440, height: 900 },
  { name: "phone", width: 390, height: 844 },
];

for (const size of SIZES) {
  for (const scheme of ["light", "dark"] as const) {
    test(`features page, ${size.name}, ${scheme}`, async ({ page }) => {
      test.setTimeout(120_000);
      await page.setViewportSize({ width: size.width, height: size.height });
      await setScheme(page, scheme);
      await page.goto("/features");
      await expect(page.locator("#start textarea")).toBeVisible();

      // Every lazy picture loaded, from the top down, before the whole page is taken.
      for (const image of await page.locator("main img:visible").all()) {
        await image.scrollIntoViewIfNeeded();
        await expect(image).toHaveJSProperty("complete", true);
      }

      await page.evaluate(() => window.scrollTo(0, 0));
      await page.screenshot({
        path: test.info().outputPath(`features-${size.name}-${scheme}.png`),
        fullPage: true,
        animations: "disabled",
      });

      // A group opened from the tabs: the tabs stay at the top, that group's current.
      await page.locator('main a[href="#decide"]').click();
      await expect(page.locator('main a[href="#decide"]')).toHaveAttribute("aria-current", "page");
      await page.screenshot({
        path: test.info().outputPath(`features-${size.name}-${scheme}-tabs.png`),
        animations: "disabled",
      });
    });
  }
}
