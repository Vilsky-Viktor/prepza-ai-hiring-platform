import { createHash, createHmac, randomBytes } from "node:crypto";

import { expect, test as base } from "@playwright/test";

import { deleteOptOuts } from "./helpers/db";
import { loaded } from "./helpers/waits";

// The page an email's unsubscribe link opens, signed out. Links are signed the way notifications
// signs them (services/notifications/app/helpers/unsubscribe.py) with EMAIL_LINK_SECRET, which
// pages.sh passes; e2e_tests/signed-in/helpers/unsubscribe.ts keeps the signed-in suite's copy.
function companyLink(email: string, companyId: string, company: string): string {
  const address = createHash("sha256").update(email).digest("hex");
  const payload = { type: "company", address, company_id: companyId, company };
  const body = Buffer.from(JSON.stringify(payload)).toString("base64url");
  const signature = createHmac("sha256", process.env.EMAIL_LINK_SECRET ?? "local-email-link-secret")
    .update(`unsubscribe:${body}`)
    .digest("base64url");

  return `/unsubscribe?token=${body}.${signature}`;
}

// A made-up company of the test's own (e2e-<id>, never a real id); its opt-outs are deleted when
// the test ends.
const test = base.extend<{ companyId: string }>({
  companyId: async ({}, use) => {
    const companyId = `e2e-${randomBytes(4).toString("hex")}`;
    await use(companyId);
    await deleteOptOuts(companyId);
  },
});

test("an invalid unsubscribe link says so and isn't indexed", async ({ page }) => {
  const response = await page.goto("/unsubscribe?token=not-a-real-link");

  expect(response?.headers()["x-robots-tag"]).toBe("noindex");
  await expect(page.getByTestId("link-invalid")).toHaveText("This unsubscribe link isn't valid.");
  await expect(page.getByRole("main").getByRole("button")).toHaveCount(0);
});

test("a candidate confirms stopping a company's emails", async ({ page, companyId }) => {
  // A made-up company and address of this test's own: nothing real is changed.
  const id = companyId.slice("e2e-".length);
  const posts: string[] = [];
  page.on("request", (request) => {
    if (request.method() === "POST" && request.url().includes("/unsubscribe/")) {
      posts.push(request.url());
    }
  });

  await page.goto(companyLink(`e2e-${id}@example.com`, `e2e-${id}`, `Acme ${id}`));
  const main = page.getByRole("main");
  // It names the company the link stops.
  await expect(main).toContainText(`Acme ${id}`);
  const title = await main.getByRole("heading", { level: 1 }).textContent();
  // Opening the link changes nothing, as mail scanners open links too: only Confirm does.
  await loaded(page);
  expect(posts).toEqual([]);

  // Confirmed: the title says it's done, and nothing is left to confirm (signed out, no settings).
  await main.getByRole("button").click();
  await expect(main.getByRole("heading", { level: 1 })).not.toHaveText(title!);
  await expect(main.getByRole("button")).toHaveCount(0);
  expect(posts).toHaveLength(1);
  await expect(main).toContainText(`Acme ${id}`);
});
