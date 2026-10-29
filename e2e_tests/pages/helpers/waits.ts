import { expect, type Locator, type Page } from "@playwright/test";

// Waits for a state instead of a fixed time: an opening dialog or a smooth scroll is measured
// once it's still, and something that never shows is checked once the page has loaded.

/** Waits until `locator` has opened (Base UI's starting style gone) and its transitions and
 * animations, and its children's, have ended, so its size and place are final. Endless ones
 * (a spinner) are left out. */
export async function settled(locator: Locator) {
  await expect(locator).not.toHaveAttribute("data-starting-style");
  await locator.evaluate((element) =>
    Promise.all(
      element
        .getAnimations({ subtree: true })
        .filter((animation) => animation.effect?.getComputedTiming().endTime !== Infinity)
        .map((animation) => animation.finished),
    ),
  );
}

/** Waits until the page hasn't scrolled for ten frames in a row. */
export async function scrollAtRest(page: Page) {
  await page.evaluate(
    () =>
      new Promise<void>((resolve) => {
        let last = window.scrollY;
        let still = 0;

        const frame = () => {
          still = window.scrollY === last ? still + 1 : 0;
          last = window.scrollY;

          if (still >= 10) {
            resolve();

            return;
          }

          requestAnimationFrame(frame);
        };

        requestAnimationFrame(frame);
      }),
  );
}

/** Waits until the page has hydrated and knows the visitor is signed out (the header's Sign in
 * shows only then), so whatever it does on load has run, nothing showing by then never will, and
 * keys pressed reach its handlers. A busy run of every worker's browser can take a while. */
export async function loaded(page: Page) {
  await expect(page.getByTestId("header-sign-in")).toBeAttached({ timeout: 60_000 });
}
