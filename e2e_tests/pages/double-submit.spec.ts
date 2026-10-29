import { expect, test } from "@playwright/test";

import { loaded } from "./helpers/waits";

// ⌘/Ctrl+Enter pressed twice before the first send finished sends the message once.
test("a contact message sent twice quickly goes once", async ({ page }) => {
  let sent = 0;
  // The first send stays unanswered until both presses are in.
  let answer = () => {};
  const answered = new Promise<void>((resolve) => (answer = resolve));
  await page.route("**/api/site/help/contact", async (route) => {
    sent += 1;
    await answered;
    await route.fulfill({ status: 204 });
  });

  await page.goto("/contact");
  await loaded(page);
  const form = page.locator("main form");
  await form.locator('input[autocomplete="name"]').fill("Ann");
  await form.locator('input[type="email"]').fill("ann@example.com");
  const message = form.locator("textarea");
  await message.fill("Hello");
  await message.press("ControlOrMeta+Enter");
  await message.press("ControlOrMeta+Enter");
  answer();

  // Sent: the reply goes to the address given.
  await expect(page.getByRole("status")).toContainText("ann@example.com");
  expect(sent).toBe(1);
});
