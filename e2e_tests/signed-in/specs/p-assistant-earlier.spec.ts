import { expect, test } from "../fixtures";
import { openPanel } from "../helpers/assistant";
import { visit } from "../helpers/navigation";
import { shot } from "../helpers/screenshots";
import { ownerEmail } from "../helpers/users";

// A long conversation opens on its latest messages; the earlier ones load on asking, above them.
// The service is stubbed in the browser (its paging is covered by the assistant's own tests).

const ID = "22222222-3333-4444-8555-666666666666";
const AT = "2026-10-09T10:00:00Z";

function message(id: string, role: "user" | "assistant", content: string) {
  return { id, role, source: "text", content, blocks: [], status: "complete", created_at: AT };
}

test("a long conversation shows its earlier messages on asking", async ({ signInAs }) => {
  const owner = await signInAs(ownerEmail());
  const saved = { id: ID, company_id: null, title: "Long chat", created_at: AT, updated_at: AT };
  await owner.route("**/api/assistant/conversations?*", (route) => route.fulfill({ json: [saved] }));
  await owner.route("**/api/assistant/conversations", (route) => route.fulfill({ json: [saved] }));
  await owner.route(`**/api/assistant/conversations/${ID}`, (route) =>
    route.fulfill({
      json: {
        ...saved,
        messages: [message("q2", "user", "And who failed?"), message("a2", "assistant", "**Bob** failed.")],
        earlier: true,
      },
    })
  );
  await owner.route(`**/api/assistant/conversations/${ID}/messages?before=q2`, (route) =>
    route.fulfill({
      json: {
        messages: [message("q1", "user", "Who passed?"), message("a1", "assistant", "**Ann** passed.")],
        earlier: false,
      },
    })
  );
  await visit(owner, "/companies");
  const panel = await openPanel(owner);
  await panel.getByTestId("assistant-history").click();
  await panel.getByRole("listitem").filter({ hasText: "Long chat" }).getByRole("button").first().click();
  await expect(panel.locator("strong", { hasText: "Bob" })).toBeVisible();
  await shot(owner, "latest-messages");

  await panel.getByTestId("earlier-messages").click();
  await expect(panel.locator("strong", { hasText: "Ann" })).toBeVisible();
  await expect(panel.getByTestId("earlier-messages")).toHaveCount(0);
  await shot(owner, "earlier-loaded");
});
