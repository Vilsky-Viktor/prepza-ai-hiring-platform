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
