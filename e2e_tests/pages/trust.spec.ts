import { expect, test } from "@playwright/test";

import { REQUEST_URL } from "./helpers/env";

type LegalDocument = { sections: { heading: string; items?: string[] }[] };

// The trust page lists the sub-processors as the data processing agreement's binding English
// text names them, in English in every language, and links to the legal pages and documents.
for (const path of ["/trust", "/de/trust"]) {
  test(`${path} shows the agreement's sub-processors and links the legal documents`, async ({
    page,
    request,
  }) => {
    const response = await request.get(`${REQUEST_URL}/api/site/help/legal/dpa?language=en`);
    expect(response.ok()).toBe(true);
    const dpa = (await response.json()) as LegalDocument;
    const expected = dpa.sections.find((section) => section.heading === "Sub-processors")?.items;
    expect(expected?.length).toBeGreaterThan(0);

    await page.goto(path);
    const main = page.getByRole("main");
    const listed = main.locator('ul[lang="en"] > li');
    await expect(listed).toHaveText(expected!);

    for (const href of ["/terms", "/privacy", "/dpa", "/documents", "/accessibility"]) {
      await expect(main.locator(`a[href$="${href}"]`).first()).toBeVisible();
    }
  });
}
