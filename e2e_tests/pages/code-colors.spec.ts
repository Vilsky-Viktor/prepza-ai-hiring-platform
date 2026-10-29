import { expect, test } from "@playwright/test";

import { REQUEST_URL } from "./helpers/env";

// A page's own code (the API docs, an AI app's MCP setup, the example agents, the home page's
// demo question) arrives colored in its HTML, so the browser never loads the highlighter for it.
for (const path of [
  "/api-docs",
  "/api-docs?tab=mcp&page=cursor",
  "/api-docs?tab=mcp&page=frameworks",
  "/",
]) {
  test(`${path} sends its code already colored`, async ({ request }) => {
    const html = await (await request.get(`${REQUEST_URL}${path}`)).text();

    expect(html).toContain("--shiki-light");
    expect(html).toContain("--shiki-dark");
  });
}
