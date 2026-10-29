import { expect, test } from "@playwright/test";

import { shot } from "./helpers/screenshots";

// A page opened from a link (here a candidate's invite) says the link is invalid only when the
// API says it's gone. Anything else (a busy or paused service, the network) offers to try again.
test("an invite that couldn't load offers to try again, and only a gone one is invalid", async ({
  page,
}) => {
  let answer = 503;
  await page.route("**/api/companies/invites/e2e-link-errors", (route) =>
    route.fulfill({
      status: answer,
      contentType: "application/json",
      body: JSON.stringify({ detail: answer === 404 ? "Invite not found" : "Busy" }),
    }),
  );

  await page.goto("/invite/e2e-link-errors");
  const failed = page.getByTestId("link-failed");
  await expect(failed).toBeVisible();
  await expect(page.getByTestId("link-invalid")).toHaveCount(0);
  await shot(page, "link-failed");

  answer = 404;
  await failed.getByRole("button").click();
  await expect(page.getByTestId("link-invalid")).toHaveText("This invite isn't valid anymore.");
  await expect(failed).toHaveCount(0);
  await shot(page, "link-invalid");
});
