import { expect, test } from "@playwright/test";

import { REQUEST_URL } from "./helpers/env";

// A page whose data is slow shows the site's frame and a spinner first: the page's segment has a
// loading state, which Next.js sends ahead of its content (and production prefetches with each
// link). The local dev server answers a prefetch with the loading state and the page together.
test("a page's loading state comes with it, ahead of its content", async ({ request }) => {
  for (const path of ["/faq", "/companies", "/practice"]) {
    const response = await request.get(`${REQUEST_URL}${path}`, {
      headers: { RSC: "1", "Next-Router-Prefetch": "1" },
    });
    const payload = await response.text();

    expect(response.status(), path).toBe(200);
    expect(payload, path).toContain('"data-testid":"page-loading"');
  }
});
