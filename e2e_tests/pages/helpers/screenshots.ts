import { type Page, test } from "@playwright/test";

/** A review screenshot in the test's results folder, taken only when SHOTS=1 (pages.sh passes it
 * on; the ui-check skill sets it): nothing compares them, and each costs a second or more. */
export async function shot(page: Page, name: string, fullPage = false) {
  if (process.env.SHOTS !== "1") {
    return;
  }

  await page.screenshot({
    path: test.info().outputPath(`${name}.png`),
    fullPage,
    animations: "disabled",
  });
}
