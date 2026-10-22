import { expect, test } from "@playwright/test";

import { REQUEST_URL } from "./helpers/env";

// The files in public/ go out with their own Cache-Control, not Next.js's max-age=0.

test("logos and pictures are kept a day, documents an hour", async ({ request }) => {
  // The /documents page may need compiling first on the local dev server.
  test.setTimeout(180_000);
  for (const path of ["/ats/greenhouse.png", "/integrations/slack.svg", "/icon.png"]) {
    const response = await request.get(`${REQUEST_URL}${path}`);

    expect(response.status(), path).toBe(200);
    expect(response.headers()["cache-control"], path).toBe("public, max-age=86400");
  }

  const document = await request.get(
    `${REQUEST_URL}/examples/prepza-candidates-example.csv`,
  );
  expect(document.headers()["cache-control"]).toBe(
    "public, max-age=3600, stale-while-revalidate=86400",
  );

  // The pages under the same names aren't files.
  const page = await request.get(`${REQUEST_URL}/documents`);
  expect(page.headers()["cache-control"]).not.toContain("max-age=3600");
});
