import { expect, test } from "../fixtures";
import { CONVERSATION, events, openPanel } from "../helpers/assistant";
import { shot } from "../helpers/screenshots";
import { ownerEmail } from "../helpers/users";

// The assistant's panel signed in: when a call fails on testee's side, the answer hands the
// user over to a person with a link to the contact page. The answer is stubbed in the browser
// (no OpenAI in tests, and no local service has to go down).

test("a call that failed on testee's side links the contact page", async ({ signInAs }) => {
  const owner = await signInAs(ownerEmail());
  await owner.route("**/api/assistant/chat", (route) =>
    route.fulfill({
      contentType: "text/event-stream",
      body: events(
        { conversation: { id: CONVERSATION } },
        { tool: { name: "get_credits", state: "running", label: "Checking credits…" } },
        { tool: { name: "get_credits", state: "failed", label: "Checking credits…" } },
        { block: { kind: "link", items: [], links: ["/contact"], page: "contact" } },
        { delta: "Your balance couldn't be read just now. Try again later." },
        { done: { message_id: "m1" } }
      ),
    })
  );
  const panel = await openPanel(owner);
  await panel.getByRole("textbox").fill("What's my credit balance?");
  await panel.locator("button[type=submit]").click();

  const contact = panel.locator('a[href$="/contact"]');
  await expect(contact).toBeVisible();
  await shot(owner, "contact-link");
  await contact.click();
  await expect(owner).toHaveURL(/\/contact$/);
});
