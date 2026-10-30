import { expect, test } from "@playwright/test";

import { loaded } from "./helpers/waits";

// Reading pages have a way back beside their title: an article to its section, the others home.
const BACK = [
  { path: "/guides/hiring-engineers", back: "/guides" },
  { path: "/compare/testgorilla", back: "/compare" },
  { path: "/about", back: "/" },
  { path: "/accessibility", back: "/" },
  { path: "/trust", back: "/" },
  { path: "/terms", back: "/" },
];

for (const { path, back } of BACK) {
  test(`${path} links back to ${back}`, async ({ page }) => {
    await page.goto(path);
    await loaded(page);
    const link = page.getByRole("main").getByTestId("back-link").getByRole("link");

    await expect(link).toHaveAttribute("href", back);
    await expect(link).toHaveAccessibleName(/\S/);
  });
}
