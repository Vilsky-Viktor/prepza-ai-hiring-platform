import { expect, test } from "@playwright/test";

// The error page's "Report": a dialog with a text field, sent to Sentry with the error.
test("the error page reports what the user was doing", async ({ page }) => {
  // An invite whose company isn't text: the page can't render it.
  await page.route("**/api/companies/invites/e2e-error-report", (route) =>
    route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({ company: { broken: true }, title: "Broken", status: "invited" }),
    }),
  );

  await page.goto("/invite/e2e-error-report");
  // The error page shows (its fixed wording isn't the test's).
  await expect(page.getByTestId("error-page")).toBeVisible();
  await page.screenshot({ path: test.info().outputPath("error-page.png") });

  await page.getByTestId("report-problem").click();
  const dialog = page.getByRole("dialog");
  // Nothing to send until something is written.
  const send = dialog.locator('button[type="submit"]');
  await expect(send).toBeDisabled();
  await dialog.getByRole("textbox").fill("Opened my invite from the email.");
  await page.screenshot({
    path: test.info().outputPath("report-dialog.png"),
    animations: "disabled",
  });
  await send.click();
  // Sent: a success notice, and the dialog closes.
  await expect(page.locator('[data-sonner-toast][data-type="success"]')).toBeVisible();
  await expect(dialog).toHaveCount(0);
});

// Retry reads the page again: once what broke it is fixed, the page shows.
test("Retry on the error page shows the page once it can be shown", async ({ page }) => {
  let broken = true;
  await page.route("**/api/companies/invites/e2e-error-retry", (route) =>
    broken
      ? route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify({ company: { broken: true }, title: "Broken", status: "invited" }),
        })
      : route.fulfill({ status: 404, json: { detail: "Invite not found" } }),
  );

  await page.goto("/invite/e2e-error-retry");
  const error = page.getByTestId("error-page");
  await expect(error).toBeVisible();
  broken = false;
  // Retry is the page's first button. A click before the page is interactive is lost, so it's
  // repeated, while the error page still shows, until the invite's page (here, a gone invite)
  // does; a click that worked may take a while to load it on a busy dev server.
  await expect(async () => {
    if (await error.isVisible()) {
      await error.getByRole("button").first().click({ timeout: 2000 });
    }

    await expect(page.getByTestId("link-invalid")).toHaveText("This invite isn't valid anymore.", {
      timeout: 5000,
    });
  }).toPass();
});

// "Report" sits in the row of the other two buttons on a computer, and on its own line under them
// on a phone.
test("the error page's report sits beside its buttons, under them on a phone", async ({ page }) => {
  await page.route("**/api/companies/invites/e2e-error-layout", (route) =>
    route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({ company: { broken: true }, title: "Broken", status: "invited" }),
    }),
  );

  for (const [size, ownLine] of [
    [{ width: 1280, height: 800 }, false],
    [{ width: 390, height: 844 }, true],
  ] as const) {
    await page.setViewportSize(size);
    await page.goto("/invite/e2e-error-layout");
    const error = page.getByTestId("error-page");
    await expect(error).toBeVisible();
    // Retry, home (a link drawn as a button), then report.
    const retry = (await error.getByRole("button").nth(0).boundingBox())!;
    const home = (await error.locator('a[href="/"]').boundingBox())!;
    const report = (await page.getByTestId("report-problem").boundingBox())!;

    expect(home.y).toBe(retry.y);

    if (ownLine) {
      expect(report.y).toBeGreaterThanOrEqual(retry.y + retry.height);
    } else {
      expect(report.y).toBe(retry.y);
      expect(report.x).toBeGreaterThan(home.x);
    }
  }
});
