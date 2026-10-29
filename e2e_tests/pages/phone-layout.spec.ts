import { expect, test } from "./helpers/templates";
import { loaded, settled } from "./helpers/waits";

// How the public pages fit a phone: wider previews, a centered footer in one column, popups
// across the screen, no keyboard hint on a touch screen. Desktop keeps its layout.

const isPhone = (name: string) => name === "phone";

// The home page's title: its two lines close together, as on desktop.
test("the home page's title lines sit close together", { tag: "@phone" }, async ({ page }) => {
  test.setTimeout(120_000);
  await page.goto("/");
  const title = page.locator("h1");
  const [lineHeight, fontSize] = await title.evaluate((element) => {
    const style = getComputedStyle(element);

    return [parseFloat(style.lineHeight), parseFloat(style.fontSize)];
  });
  expect(lineHeight).toBe(fontSize);
});

// On phones the footer is one centered column; on desktop its links stand in three columns.
test("the footer is one centered column on phones", { tag: "@phone" }, async ({ page }, info) => {
  await page.goto("/faq");
  const footer = page.getByRole("contentinfo");
  const links = footer.getByRole("navigation").getByRole("link");
  const lefts = await links.evaluateAll((elements) =>
    elements.map((element) => Math.round(element.getBoundingClientRect().left)),
  );
  const columns = new Set(lefts).size;

  if (!isPhone(info.project.name)) {
    expect(columns).toBe(3);

    return;
  }

  const width = page.viewportSize()!.width;
  const centers = await links.evaluateAll((elements) =>
    elements.map((element) => {
      const box = element.getBoundingClientRect();

      return box.left + box.width / 2;
    }),
  );

  for (const center of centers) {
    expect(Math.abs(center - width / 2)).toBeLessThan(4);
  }

  const icon = footer.locator('[role="img"] svg').first();
  expect((await icon.boundingBox())!.width).toBe(32);
  await expect(footer.locator("[data-assistant-toggle]")).toHaveCSS(
    "height",
    "48px",
  );
});

// On phones a dialog spans the screen's width, with square corners.
test("a dialog spans a phone's width", { tag: "@phone" }, async ({ page }, info) => {
  test.setTimeout(120_000);
  await page.goto("/");
  await page.getByTestId("page-help").filter({ visible: true }).click();
  const dialog = page.getByRole("dialog");
  await expect(dialog).toBeVisible();
  // It finishes opening first.
  await settled(dialog);
  const box = (await dialog.boundingBox())!;

  if (isPhone(info.project.name)) {
    expect(Math.round(box.x)).toBe(0);
    expect(Math.round(box.width)).toBe(page.viewportSize()!.width);
    await expect(dialog).toHaveCSS("border-top-left-radius", "0px");
    // The help fills the screen, and Close is in sight without scrolling, and after it.
    expect(Math.round(box.height)).toBe(page.viewportSize()!.height);
    const close = dialog.locator('[data-slot="dialog-footer"] button');
    await expect(close).toBeInViewport();
    await dialog.evaluate((element) => element.scrollBy(0, 2_000));
    await expect(close).toBeInViewport();
  } else {
    expect(box.x).toBeGreaterThan(0);
    await expect(dialog).not.toHaveCSS("border-top-left-radius", "0px");
  }
});

// "⌘/Ctrl + Enter to send" only where there's a keyboard: not on a touch screen.
test("the send shortcut hint shows only without a touch screen", { tag: "@phone" }, async ({
  page,
}, info) => {
  await page.goto("/contact");
  // The hint under the message.
  const hint = page.locator("main form textarea + p");

  if (isPhone(info.project.name)) {
    await expect(hint).toBeHidden();
  } else {
    await expect(hint).toBeVisible();
  }
});

// On phones the home page's box to start in and the price lists reach the screen's edges.
test("the home page's box and the prices span a phone's width", { tag: "@phone-only" }, async ({
  page,
}) => {
  test.setTimeout(120_000);
  const width = page.viewportSize()!.width;

  await page.goto("/");
  const start = page.locator("main form").first();
  const startBox = (await start.boundingBox())!;
  expect(Math.round(startBox.x)).toBe(0);
  expect(Math.round(startBox.width)).toBe(width);

  await page.goto("/pricing");
  const prices = (await page.locator("main ul").first().boundingBox())!;
  expect(Math.round(prices.x)).toBe(0);
  expect(Math.round(prices.width)).toBe(width);
});

// Opening the home page doesn't put the cursor in its box: on a phone the keyboard would cover
// the page.
test("the home page's box isn't focused on load", { tag: "@phone" }, async ({ page }) => {
  test.setTimeout(120_000);
  await page.goto("/");
  await loaded(page);
  await expect(page.locator("main textarea").first()).not.toBeFocused();
});

// On phones a test's practice page has its level and language under the title, then its start.
test("a practice page starts under its tags on a phone", { tag: "@phone-only" }, async ({
  page,
  addTemplate,
}) => {
  test.setTimeout(120_000);
  const template = await addTemplate();
  await page.goto(`/practice/${template.slug}`);
  const tags = (await page
    .locator("main [data-slot=badge]")
    .first()
    .boundingBox())!;
  const start = (await page.getByTestId("start-practice").boundingBox())!;
  expect(start.y).toBeGreaterThan(tags.y + tags.height);
});

// The header's logo link is named by what it shows ("p." on a phone, the whole logo on a wider
// screen) and then where it leads, so a voice user can say what they see (WCAG 2.5.3).
test("the header's logo link is named by its visible text", { tag: "@phone" }, async ({ page }) => {
  await page.goto("/");
  const logo = page.getByRole("banner").getByRole("link").first();
  // The logo itself, as drawn: letters hidden on a phone aren't in its text.
  const shown = (await logo.locator("span").first().innerText()).replace(/\s/g, "");
  expect(shown.length).toBeGreaterThan(0);
  const letters = [...shown].map((letter) => letter.replace(/[.*+?^${}()|[\]\\]/g, "\\$&"));
  await expect(logo).toHaveAccessibleName(new RegExp(`^${letters.join("\\s*")}\\s+\\S`));
});
