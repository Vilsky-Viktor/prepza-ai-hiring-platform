import { expect, test } from "@playwright/test";

import { REQUEST_URL } from "./helpers/env";
import { loaded, settled } from "./helpers/waits";

// The home page's info button, beside the demos (under the promise on phones), opens a guide to
// how testee works in a dialog that closes again.
test("the home page's info button opens its guide", async ({ page }) => {
  // The local dev server compiles the home page on first open.
  test.setTimeout(120_000);
  await page.goto("/");
  await loaded(page);
  const button = page.getByTestId("page-help").filter({ visible: true });
  await expect(button).toHaveCount(1);
  // An icon alone: its label is what screen readers read.
  await expect(button).toHaveAccessibleName(/.+/);

  // Hovering opens its tooltip (again if the first hover came before the page was ready).
  await expect(async () => {
    await page.mouse.move(0, 0);
    await button.hover();
    await expect(button).toHaveAttribute("data-popup-open", { timeout: 2_000 });
  }).toPass();

  // While the guide loads, the dialog shows the loading mark; the guide's reply is held until
  // the mark has been seen.
  let release!: () => void;
  const held = new Promise<void>((resolve) => (release = resolve));
  await page.route("**/site/help/pages/**", async (route) => {
    await held;
    await route.continue();
  });
  await button.click();
  const dialog = page.getByRole("dialog");
  await expect(dialog).toBeVisible();
  await expect(dialog.getByTestId("page-loading")).toBeVisible();
  release();
  await expect(dialog.getByTestId("page-loading")).toBeHidden();
  // What it's for, then two lists: what to do there, and tips.
  await expect(dialog.getByRole("heading").first()).not.toBeEmpty();
  await expect(dialog.getByRole("list")).toHaveCount(2);

  for (const list of await dialog.getByRole("list").all()) {
    expect(await list.getByRole("listitem").count()).toBeGreaterThan(0);
  }

  await dialog.locator('[data-slot="dialog-footer"] button').click();
  await expect(dialog).toBeHidden();
});

// Every guide ends with a card across the whole dialog asking for problems, ideas and missing
// features, whose button opens the contact page.
test("the guide's feedback card leads to the contact page", async ({ page }) => {
  // The local dev server compiles the home page and the contact page on first open.
  test.setTimeout(120_000);
  await page.goto("/");
  await loaded(page);
  await page.getByTestId("page-help").filter({ visible: true }).click();
  const dialog = page.getByRole("dialog");
  await expect(dialog).toBeVisible();
  await settled(dialog);

  const card = dialog.getByTestId("page-help-feedback");
  await expect(card).toBeVisible();
  // Edge to edge: as wide as the dialog's body, its padding left out.
  const [width, bodyWidth] = await card.evaluate((element) => [
    element.getBoundingClientRect().width,
    element.parentElement!.clientWidth,
  ]);
  expect(Math.round(width)).toBe(bodyWidth);

  const link = card.getByRole("link");
  await expect(link).toHaveCount(1);
  await expect(link).toHaveAccessibleName(/.+/);
  await link.click();
  await expect(page).toHaveURL(/\/contact$/);
  await expect(dialog).toBeHidden();
});

// The home page's guide links the guide article on writing a job description, in the page's
// language: the article the site names for it, which opens.
for (const locale of ["en", "de"]) {
  test(`the home page's guide links its guide article (${locale})`, async ({ page }) => {
    // The local dev server compiles the home page and the guide on first open.
    test.setTimeout(120_000);
    const response = await page.request.get(`${REQUEST_URL}/api/site/help/pages/landing`, {
      headers: { "Accept-Language": locale },
    });
    const { article } = (await response.json()) as {
      article: { title: string; path: string; language: string };
    };
    expect(article.language).toBe(locale);
    const prefix = locale === "en" ? "" : `/${locale}`;

    await page.goto(prefix || "/");
    await loaded(page);
    await page.getByTestId("page-help").filter({ visible: true }).click();
    const link = page.getByRole("dialog").getByRole("link", { name: article.title });
    await expect(link).toHaveAttribute("href", `${prefix}${article.path}`);
    await link.click();
    await expect(page).toHaveURL(new RegExp(`${prefix}${article.path}$`), { timeout: 30_000 });
    await expect(page.getByRole("heading", { level: 1 })).toHaveText(article.title);
  });
}
