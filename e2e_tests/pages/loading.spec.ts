import { expect, test } from "@playwright/test";

import { REQUEST_URL } from "./helpers/env";

// A company's pages, which wait on services that may be asleep, show the site's frame and a
// spinner first: their segment has a loading state, which Next.js sends ahead of the content
// (production prefetches it with each link; the local dev server answers a prefetch with both).
// Public pages have none, so a missing one still answers 404.

async function prefetch(request: import("@playwright/test").APIRequestContext, path: string) {
  const response = await request.get(`${REQUEST_URL}${path}`, {
    headers: { RSC: "1", "Next-Router-Prefetch": "1" },
  });

  return response.text();
}

test("a company's pages come with their loading state", async ({ request }) => {
  for (const path of [
    "/companies",
    "/companies/00000000-0000-0000-0000-000000000000/interviews",
    "/companies/00000000-0000-0000-0000-000000000000/interviews/00000000-0000-0000-0000-000000000000",
  ]) {
    expect(await prefetch(request, path), path).toContain('"data-testid":"page-loading"');
  }
});

test("public pages have no loading state", async ({ request }) => {
  for (const path of ["/faq", "/pricing"]) {
    expect(await prefetch(request, path), path).not.toContain('"data-testid":"page-loading"');
  }
});
