import type { Locator, Page, Route } from "@playwright/test";

import { expect, test } from "../fixtures";
import { assistantAnswers, CONVERSATION, events, openPanel } from "../helpers/assistant";
import { visit } from "../helpers/navigation";
import { shot } from "../helpers/screenshots";
import { ownerEmail } from "../helpers/users";

// Thumbs up and down under Mira's answers, signed in (the assistant) and signed out (the
// help chat). Answers are stubbed in the browser (no OpenAI in tests), and so are the votes'
// saves, which the services' own tests cover against the database; here: what's sent, what
// the buttons show, a failed save, and a saved vote shown again after a reload.

// The vote buttons, in their order: thumbs up, then down.
const UP = 0;
const DOWN = 1;
const HELP_ANSWER = {
  id: "c87785d7-1ace-4a4c-9e4b-7c9b93a6387a",
  trace_id: "15e22744a64a4538a7da68ffb20c114a",
  signature: "5f707ada016746672280c6d632721631c7af796222f981ce303d1113e36475ef",
};

/** The votes the page saves at `pattern`, by their bodies; each answered with `status`. */
async function savedVotes(page: Page, pattern: string, status = { code: 204 }) {
  const sent: unknown[] = [];
  await page.route(pattern, (route: Route) => {
    sent.push(route.request().postDataJSON());

    return route.fulfill({ status: status.code });
  });

  return sent;
}

function thumb(votes: Locator, index: number) {
  return votes.getByRole("button").nth(index);
}

async function ask(panel: Locator, question: string) {
  await panel.getByRole("textbox").fill(question);
  await panel.locator("button[type=submit]").click();
}

test("a member votes on the assistant's answers, changes and clears the vote", async ({
  signInAs,
}) => {
  const owner = await signInAs(ownerEmail());
  await visit(owner, "/companies");
  const panel = await openPanel(owner);
  await assistantAnswers(owner);
  const status = { code: 204 };
  const sent = await savedVotes(
    owner,
    `**/api/assistant/conversations/${CONVERSATION}/messages/m1/vote`,
    status
  );
  await ask(panel, "Who passed?");
  // The stubbed answer, not one from the service.
  await expect(panel.locator("strong", { hasText: "Ann" })).toBeVisible();
  const votes = panel.getByTestId("answer-vote");
  await expect(votes).toBeVisible();
  await expect(thumb(votes, UP)).toHaveAttribute("aria-pressed", "false");
  await expect(thumb(votes, DOWN)).toHaveAttribute("aria-pressed", "false");

  await thumb(votes, UP).click();
  await expect(thumb(votes, UP)).toHaveAttribute("aria-pressed", "true");
  await shot(owner, "voted-up");
  // The other thumb changes it; the same one again clears it.
  await thumb(votes, DOWN).click();
  await expect(thumb(votes, DOWN)).toHaveAttribute("aria-pressed", "true");
  await expect(thumb(votes, UP)).toHaveAttribute("aria-pressed", "false");
  await thumb(votes, DOWN).click();
  await expect(thumb(votes, DOWN)).toHaveAttribute("aria-pressed", "false");
  await expect.poll(() => sent).toEqual([{ value: 1 }, { value: -1 }, { value: null }]);

  // A vote that couldn't be saved goes back as it was, with an error.
  status.code = 500;
  await thumb(votes, UP).click();
  await expect(owner.locator('[data-sonner-toast][data-type="error"]')).toBeVisible();
  await expect(thumb(votes, UP)).toHaveAttribute("aria-pressed", "false");

  // A saved vote shows when the conversation comes back after a reload.
  await owner.route(`**/api/assistant/conversations/${CONVERSATION}`, (route) =>
    route.fulfill({
      json: {
        id: CONVERSATION,
        company_id: null,
        title: "Who passed?",
        created_at: "2026-10-09T10:00:00Z",
        updated_at: "2026-10-09T10:00:00Z",
        messages: [
          { id: "q", role: "user", source: "text", content: "Who passed?", blocks: [], status: "complete", vote: null, created_at: "2026-10-09T10:00:00Z" },
          { id: "m1", role: "assistant", source: "text", content: "Ann passed.", blocks: [], status: "complete", vote: -1, created_at: "2026-10-09T10:00:00Z" },
        ],
      },
    })
  );
  await owner.reload();
  const restored = owner.getByRole("dialog").getByTestId("answer-vote");
  await expect(thumb(restored, DOWN)).toHaveAttribute("aria-pressed", "true");
  await expect(thumb(restored, UP)).toHaveAttribute("aria-pressed", "false");
});

test("a visitor votes on the help chat's answers with the answer's signature", async ({
  browser,
}) => {
  const page = await (await browser.newContext()).newPage();
  await page.route("**/api/assistant/help/chat", (route) =>
    route.fulfill({
      contentType: "text/event-stream",
      body: events(
        { delta: "Paste a job description." },
        { done: true, signature: "abc", answer: HELP_ANSWER }
      ),
    })
  );
  const sent = await savedVotes(page, `**/api/assistant/help/answers/${HELP_ANSWER.id}/vote`);
  await visit(page, "/");
  const panel = await openPanel(page);
  await ask(panel, "How do I start?");
  const votes = panel.getByTestId("answer-vote");

  await thumb(votes, DOWN).click();
  await expect(thumb(votes, DOWN)).toHaveAttribute("aria-pressed", "true");
  await shot(page, "visitor-voted-down");
  await thumb(votes, DOWN).click();
  await expect(thumb(votes, DOWN)).toHaveAttribute("aria-pressed", "false");

  const answer = { trace_id: HELP_ANSWER.trace_id, signature: HELP_ANSWER.signature };
  await expect.poll(() => sent).toEqual([
    { ...answer, value: -1 },
    { ...answer, value: null },
  ]);
  await page.context().close();
});
