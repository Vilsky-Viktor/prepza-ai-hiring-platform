import { expect, test } from "@playwright/test";

import { REQUEST_URL } from "./helpers/env";

// A page's own code (the API docs, the home page's demo question) arrives colored in its HTML,
// so the browser never loads the highlighter for it.
for (const path of ["/api-docs", "/api-docs?tab=mcp", "/"]) {
  test(`${path} sends its code already colored`, async ({ request }) => {
    const html = await (await request.get(`${REQUEST_URL}${path}`)).text();

    expect(html).toContain("--shiki-light");
    expect(html).toContain("--shiki-dark");
  });
}

// Code keeps its own size on Chinese, Japanese and Korean pages, so the home page's example
// scrolls inside its block and never past a phone's screen.
for (const locale of ["ja", "zh", "ko"]) {
  test(`the home page's code fits a phone's screen in ${locale}`, async ({ page }) => {
    test.setTimeout(120_000);
    await page.setViewportSize({ width: 390, height: 844 });
    await page.goto(`/${locale}`);
    const code = page.getByRole("main").locator("pre code").first();
    await expect(code).toBeAttached();

    const right = await code.evaluate((element) => element.getBoundingClientRect().right);
    expect(right).toBeLessThanOrEqual(390);
  });
}
