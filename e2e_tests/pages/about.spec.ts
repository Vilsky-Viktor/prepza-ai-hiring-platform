import { expect, test } from "@playwright/test";

// The about page's photo downloads in a size that fits how wide it's shown, not the file's.
test("the founder's photo comes in the size it's shown at", async ({ page }) => {
  await page.goto("/about");
  const photo = page.getByRole("main").locator("figure img");
  // Loaded lazily, once it's near the screen.
  await photo.scrollIntoViewIfNeeded();
  await expect(photo).toHaveJSProperty("complete", true);

  const { asked, shown } = await photo.evaluate((image: HTMLImageElement) => ({
    asked: Number(new URL(image.currentSrc, location.href).searchParams.get("w")),
    shown: image.clientWidth * devicePixelRatio,
  }));

  expect(asked).toBeGreaterThanOrEqual(shown);
  expect(asked).toBeLessThan(shown * 2);
});
