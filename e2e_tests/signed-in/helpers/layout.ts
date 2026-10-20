import { expect, type Locator } from "@playwright/test"

// A phone's screen, for the phone layouts.
export const PHONE = { width: 390, height: 844 }

/** Where `locator` is on the page, in whole pixels. */
export async function box(locator: Locator) {
  const found = (await locator.boundingBox({ timeout: 15_000 }))!

  return {
    left: Math.round(found.x),
    top: Math.round(found.y),
    width: Math.round(found.width),
    height: Math.round(found.height),
    right: Math.round(found.x + found.width),
    bottom: Math.round(found.y + found.height),
  }
}

/** Waits until `locator` has opened (Base UI's starting style gone) and its transitions and
 * animations, and its children's, have ended, so its size and place are final. Endless ones
 * (a spinner) are left out. */
export async function settled(locator: Locator) {
  await expect(locator).not.toHaveAttribute("data-starting-style")
  await locator.evaluate((element) =>
    Promise.all(
      element
        .getAnimations({ subtree: true })
        .filter((animation) => animation.effect?.getComputedTiming().endTime !== Infinity)
        .map((animation) => animation.finished)
    )
  )
}
