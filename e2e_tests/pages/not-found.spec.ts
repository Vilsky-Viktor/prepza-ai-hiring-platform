import { expect, test } from "@playwright/test";

import { REQUEST_URL } from "./helpers/env";

// A page that doesn't exist, or that the visitor may not see, answers a real 404, so search
// engines never index it as a page and the admin zone stays hidden.
test("missing public pages and the admin zone answer 404", async ({ request }) => {
  for (const path of [
    "/no-such-page",
    "/guides/no-such-guide",
    "/de/compare/no-such-comparison",
    "/superadmin/templates",
    "/superadmin/support",
  ]) {
    const response = await request.get(`${REQUEST_URL}${path}`, { maxRedirects: 0 });

    expect(response.status(), path).toBe(404);
  }
});
