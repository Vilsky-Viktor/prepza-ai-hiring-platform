import { expect, type Page } from "@playwright/test";

/** Stops the page's clock (installed with `page.clock.install()`) a second from now, so time
 * moves only as the test runs it. The page's time is read again if a busy page let it pass that
 * second before the clock was stopped. */
export async function pauseClock(page: Page) {
  await expect(async () => {
    const now = await page.evaluate(() => Date.now());
    await page.clock.pauseAt(now + 1_000);
  }).toPass();
}
