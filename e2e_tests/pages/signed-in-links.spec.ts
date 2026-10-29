import { expect, test } from "@playwright/test";

import { shot } from "./helpers/screenshots";

const company = "8d0f3c1e-1111-4222-8333-944455556666";
const interview = "1b4e28ba-2fa1-11d2-883f-0016d3cca427";

// Links into a company's pages (a scorecard from an ATS, Slack or an email, an interview, a
// template, a generation) opened signed out ask to sign in, instead of "Page not found".
const pages = [
  `/companies/${company}/interviews/${interview}/candidates/${interview}`,
  `/companies/${company}/interviews/${interview}`,
  `/companies/${company}/interviews/${interview}/try`,
  `/companies/${company}/interviews/new`,
  `/companies/${company}/templates/${interview}`,
  `/generate/${interview}?next=/companies/${company}/interviews/${interview}`,
];

for (const path of pages) {
  test(`signed out, ${path.split("?")[0]} asks to sign in`, async ({ page }) => {
    const response = await page.goto(path);
    await expect(page.getByRole("main").getByTestId("sign-in-google")).toBeVisible();
    // The page itself, not the not-found page.
    expect(response?.status()).not.toBe(404);
  });
}

test("a scorecard link opened signed out", async ({ page }) => {
  await page.goto(pages[0]);
  await expect(page.getByRole("main").getByTestId("sign-in-google")).toBeVisible();
  await shot(page, "scorecard-signed-out");
});
