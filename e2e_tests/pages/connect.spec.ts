import { expect, test } from "@playwright/test";

import { loaded } from "./helpers/waits";

// The page an AI app sends a user to, to allow it the use of their account, signed out. Without
// a request it says the link expired; with one it asks to sign in first. It's never
// indexed.
test("the AI app consent page without a request says the link expired", async ({ page }) => {
  const response = await page.goto("/connect");

  expect(response?.headers()["x-robots-tag"]).toBe("noindex");
  const main = page.getByRole("main");
  // The notice alone: no title or way to sign in.
  await expect(main.getByRole("status")).toContainText("This link has expired or was already used.");
  await expect(main.getByRole("heading")).toHaveCount(0);
  await expect(main.getByRole("button")).toHaveCount(0);
});

test("the AI app consent page asks to sign in first", async ({ page }) => {
  // The API tells the request's app only to a signed-in user.
  const response = await page.goto("/connect?request=e2e-unknown");

  expect(response?.headers()["x-robots-tag"]).toBe("noindex");
  const main = page.getByRole("main");
  await expect(main.getByRole("heading", { level: 1 })).toBeVisible();
  await loaded(page);
  await main.getByRole("button").click();
  await expect(page.getByRole("dialog").getByTestId("sign-in-google")).toBeVisible();
});

// Signed out, the request isn't read: the API answers about it only to a signed-in user.
test("the AI app consent page signed out doesn't read the request", async ({ page }) => {
  const reads: string[] = [];
  page.on("request", (request) => {
    if (request.url().includes("/assistant/connect/")) {
      reads.push(request.url());
    }
  });

  await page.goto("/connect?request=e2e-request");
  await expect(page.getByRole("main").getByRole("button")).toBeVisible();
  // Loaded and knowing the visitor is signed out: whatever it reads on load, it has asked for.
  await loaded(page);
  expect(reads).toEqual([]);
});
