import { expect, test } from "@playwright/test";

import { loaded } from "./helpers/waits";

// The signed-out pages (the signed-in ones: e2e_tests/signed-in), on a desktop and a phone.
const PAGES = [
  "/",
  "/companies",
  "/features",
  "/pricing",
  "/terms",
  "/privacy",
  "/documents",
  "/faq",
  "/about",
  "/contact",
  "/accessibility",
  "/trust",
  "/practice",
  "/tests",
  "/compare",
  "/guides",
  "/pre-employment-testing",
  "/ai-interviews",
  "/compare/testgorilla",
  "/guides/hiring-engineers",
  "/de/pricing",
];
// Articles keep their headings' capitals (names such as TestGorilla or EU).
const ARTICLES = [
  "/pre-employment-testing",
  "/ai-interviews",
  "/compare/testgorilla",
  "/guides/hiring-engineers",
];
// The width every page's <main> has: max-w-page, 80rem (CLAUDE.md, rule 6).
const MAIN_MAX_WIDTH = 1280;

for (const path of PAGES) {
  test(`${path} loads cleanly and follows the layout rules`, { tag: "@phone" }, async ({
    page,
  }) => {
    const errors: string[] = [];
    page.on("console", (message) => {
      if (message.type() === "error") {
        errors.push(message.text());
      }
    });
    page.on("pageerror", (error) => errors.push(error.message));

    const response = await page.goto(path);
    await loaded(page);

    expect(response?.status()).toBe(200);
    expect(errors).toEqual([]);

    const layout = await page.evaluate(() => {
      const root = document.documentElement;
      const footer = document.querySelector("footer")!.getBoundingClientRect();
      const heading = document.querySelector("h1");
      const input = document.querySelector("textarea");

      return {
        viewport: window.innerWidth,
        scrollWidth: root.scrollWidth,
        clientWidth: root.clientWidth,
        // The page's room: the window less the scroll bar's gutter, which stays reserved.
        bodyWidth: document.body.getBoundingClientRect().width,
        scrollHeight: root.scrollHeight,
        innerHeight: window.innerHeight,
        footerBottom: footer.bottom + window.scrollY,
        mainWidth: document.querySelector("main")!.getBoundingClientRect()
          .width,
        headingCase: heading
          ? getComputedStyle(heading).textTransform
          : "lowercase",
        inputBottom: input ? input.getBoundingClientRect().bottom : 0,
      };
    });

    // Nothing wider than the window, on a phone too.
    expect(layout.scrollWidth).toBeLessThanOrEqual(layout.clientWidth);
    // Every page is as wide as the header: its full width, or all the room beside the scroll bar.
    expect(layout.mainWidth).toBe(Math.min(MAIN_MAX_WIDTH, layout.bodyWidth));
    // The footer ends the page.
    expect(
      Math.abs(layout.footerBottom - layout.scrollHeight),
    ).toBeLessThanOrEqual(1);
    // The home page's input is on the first screen, above the landing sections.
    if (path === "/") {
      expect(layout.inputBottom).toBeLessThanOrEqual(layout.innerHeight);
    }

    // Titles are lowercase, like the logo; articles keep their capitals.
    expect(layout.headingCase).toBe(
      ARTICLES.includes(path) ? "none" : "lowercase",
    );
    // In the interface's language: German under /de.
    await expect(page.locator("html")).toHaveAttribute(
      "lang",
      path.startsWith("/de") ? "de" : "en",
    );
    await expect(page.getByRole("banner").getByTestId("header-sign-in")).toBeVisible();
  });
}

// The Japanese, Chinese and Korean fonts (hundreds of character ranges) come only with pages in
// those languages, and draw their text there.
test("only Japanese, Chinese and Korean pages load their fonts", async ({
  page,
}) => {
  const cjkFontFaces = () =>
    page.evaluate(
      () =>
        [...document.styleSheets]
          .flatMap((sheet) => [...sheet.cssRules])
          .filter(
            (rule) =>
              rule instanceof CSSFontFaceRule &&
              /Noto Sans (JP|SC|KR)/.test(rule.style.fontFamily),
          ).length,
    );

  await page.goto("/pricing");
  expect(await cjkFontFaces()).toBe(0);

  await page.goto("/ja/pricing");
  expect(await cjkFontFaces()).toBeGreaterThan(0);
  const font = await page.evaluate(
    () => getComputedStyle(document.querySelector("h1")!).fontFamily,
  );
  expect(font).toContain("Noto Sans JP");
});

// Signing in offers two email boxes, both unticked: product updates can be declined, offers are
// sent only when asked for.
test("the sign-in dialog offers the email boxes, unticked", async ({ page }) => {
  await page.goto("/");
  const dialog = page.getByRole("dialog");

  await expect(async () => {
    await page.getByRole("banner").getByTestId("header-sign-in").click();
    await expect(dialog).toBeVisible({ timeout: 2_000 });
  }).toPass();
  await expect(dialog.getByTestId("email-box-noUpdates")).not.toBeChecked();
  await expect(dialog.getByTestId("email-box-promotions")).not.toBeChecked();
});
