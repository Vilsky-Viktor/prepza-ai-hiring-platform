import { expect, test } from "../fixtures";
import { createCompany } from "../helpers/api";
import { assistantAnswers, CANDIDATE_LINK, CONVERSATION, events, openPanel } from "../helpers/assistant";
import { visit } from "../helpers/navigation";
import { shot } from "../helpers/screenshots";
import { ownerEmail } from "../helpers/users";

// The assistant's panel signed in: the welcome for the user's stage (the real service), an
// answer with a candidate row, voice with Chrome's fake microphone, the history, and a reload
// in the middle of a chat; and a visitor who signs in from the sign-in card keeps their chat.
// Answers and transcripts are stubbed in the browser: no OpenAI in tests. Actions and pasted
// secrets are in p-assistant-actions.

// Chrome's fake microphone, beside the host rules the config sets.
test.use({
  launchOptions: {
    args: [
      ...(process.env.HOST_RULES ? [`--host-resolver-rules=${process.env.HOST_RULES}`] : []),
      "--use-fake-device-for-media-stream",
      "--use-fake-ui-for-media-stream",
    ],
  },
});

test("the assistant welcomes by stage, answers, takes voice, keeps history and survives a reload", async ({
  signInAs,
}) => {
  const owner = await signInAs(ownerEmail());
  let panel = await openPanel(owner);
  // Open, the input is ready to type in.
  await expect(panel.getByRole("textbox")).toBeFocused();

  // No company yet, then a company that isn't verified: the service decides the stage.
  await expect(panel.getByTestId("welcome-no_company")).toBeVisible();
  // The welcome introduces the assistant by name, kept as written in the lowercase title.
  await expect(panel.getByTestId("welcome-no_company").getByRole("heading").locator(".normal-case").first()).toBeVisible();
  await shot(owner, "welcome-no-company");
  await panel.getByTestId("assistant-close").click();
  const company = await createCompany(owner);
  panel = await openPanel(owner);
  await expect(panel.getByTestId("welcome-unverified")).toBeVisible();

  // The company picker: all companies outside a company's pages, the page's company on them.
  const picker = panel.getByTestId("assistant-company").getByRole("button");
  await expect(picker).toBeVisible();
  await expect(picker).not.toHaveText(company.name);
  await panel.getByTestId("assistant-close").click();
  await visit(owner, `/companies/${company.id}/interviews`);
  panel = await openPanel(owner);
  await expect(picker).toHaveText(company.name);

  // An answer: the tool at work, the markdown, and the candidate's row linking to their page.
  const sent = await assistantAnswers(owner);
  await panel.getByRole("textbox").fill("Who passed?");
  await panel.locator("button[type=submit]").click();
  await expect(panel.locator("strong", { hasText: "Ann" })).toBeVisible();
  await expect(panel.locator(`a[href="${CANDIDATE_LINK}"]`)).toContainText("ann@example.com");
  // One link, named by what it opens.
  const interview = panel.locator('a[href="/companies/c/interviews/i"]');
  await expect(interview).toHaveCount(1);
  await expect(interview).toContainText("Senior Backend");
  await shot(owner, "answer");
  expect(sent[0]).toMatchObject({
    message: "Who passed?",
    source: "text",
    company_id: company.id,
    earlier: [],
  });

  // Picking all companies (the menu's first choice) sends no company with the next message.
  await picker.click();
  await owner.getByRole("menuitemradio").first().click();
  await expect(picker).not.toHaveText(company.name);

  // Voice from the keyboard: Enter starts, Enter stops; the transcript is sent as the message.
  // The page's clock is Playwright's, so a long enough recording takes no time.
  await owner.clock.install();
  await owner.route("**/api/assistant/transcribe", (route) => {
    expect(route.request().headers()["content-type"]).toMatch(/^audio\//);

    return route.fulfill({ json: { text: "Who else passed?" } });
  });
  // The microphone: the input's pressable button.
  const mic = panel.locator("form button[aria-pressed]");
  await mic.focus();
  await owner.keyboard.press("Enter");
  await expect(mic).toHaveAttribute("aria-pressed", "true");
  await shot(owner, "recording");
  await owner.clock.fastForward(1_200);
  await owner.keyboard.press("Enter");
  await expect(panel.getByRole("list").getByText("Who else passed?")).toBeVisible();
  expect(sent[1]).toMatchObject({ message: "Who else passed?", source: "voice", conversation_id: CONVERSATION });
  expect(sent[1].company_id).toBeUndefined();

  // Esc cancels a recording without closing the panel; nothing is sent.
  await mic.focus();
  await owner.keyboard.press("Enter");
  await expect(mic).toHaveAttribute("aria-pressed", "true");
  await owner.keyboard.press("Escape");
  await expect(mic).toHaveAttribute("aria-pressed", "false");
  await expect(panel).toBeVisible();
  expect(sent).toHaveLength(2);

  // A click beside the panel closes it; reopened, the conversation is still there.
  await owner.mouse.click(100, 500);
  await expect(panel).toHaveCount(0);
  panel = await openPanel(owner);
  await expect(panel.getByRole("list").getByText("Who else passed?")).toBeVisible();

  // Its width: wider with the arrow keys, no narrower than 360px however far it's dragged.
  const handle = panel.getByRole("separator");
  const width = async () => (await panel.boundingBox())!.width;
  await expect.poll(width).toBe(448);
  await shot(owner, "width-default");
  await handle.focus();
  await owner.keyboard.press("ArrowLeft");
  await owner.keyboard.press("ArrowLeft");
  await expect.poll(width).toBe(480);
  const box = (await handle.boundingBox())!;
  await owner.mouse.move(box.x + box.width / 2, box.y + 300);
  await owner.mouse.down();
  await owner.mouse.move(200, box.y + 300, { steps: 5 });
  await owner.mouse.up();
  await expect.poll(width).toBe(896);
  await shot(owner, "width-wide");
  const wide = (await handle.boundingBox())!;
  await owner.mouse.move(wide.x + wide.width / 2, wide.y + 300);
  await owner.mouse.down();
  await owner.mouse.move(1270, wide.y + 300, { steps: 5 });
  await owner.mouse.up();
  await expect.poll(width).toBe(360);
  await shot(owner, "width-narrow");

  // A reload in the middle of the chat brings the panel and the conversation back.
  await owner.reload();
  panel = owner.getByRole("dialog");
  await expect(panel.getByRole("list").getByText("Who passed?")).toBeVisible();
  // The pick and the width came back with it.
  await expect(panel.getByTestId("assistant-company").getByRole("button")).not.toHaveText(company.name);
  await expect.poll(async () => (await panel.boundingBox())!.width).toBe(360);

  // The history lists it; deleting asks first.
  await panel.getByTestId("assistant-history").click();
  const chat = panel.getByRole("listitem").filter({ hasText: "Who passed?" });
  await expect(chat).toBeVisible();
  // Hovering a chat shows its whole title, above the panel (the tooltip has no ARIA role: it
  // repeats the row's own text), and the panel stays open.
  await chat.getByRole("button").first().hover();
  const tooltip = owner.locator("[data-side][data-open][tabindex]", { hasText: /^Who passed\?$/ });
  await expect(tooltip).toBeVisible();
  await expect(tooltip).toBeInViewport();
  await expect(panel).toBeVisible();
  await shot(owner, "history");
  // Its bin, the row's last button; the question opens over the panel.
  await chat.getByRole("button").last().click();
  await owner.getByRole("dialog").last().getByRole("button").last().click();
  await expect(chat).toHaveCount(0);

  // New chat starts over, with the input ready again. With no recent conversation (the service
  // says none, as for one older than its window), a reload leaves the panel closed, and it
  // opens on the welcome.
  await panel.getByTestId("assistant-new-chat").click();
  await expect(panel.getByRole("textbox")).toBeFocused();
  await owner.reload();
  await expect(owner.getByRole("banner").locator("[data-assistant-toggle]")).toBeVisible();
  await expect(owner.getByRole("dialog")).toHaveCount(0);
  panel = await openPanel(owner);
  await expect(panel.getByTestId("welcome-unverified")).toBeVisible();
});

test("a visitor who signs in from the sign-in card keeps their chat", async ({ browser }) => {
  const context = await browser.newContext();
  const page = await context.newPage();
  await page.route("**/api/rounds/help/chat", (route) =>
    route.fulfill({
      contentType: "text/event-stream",
      body: events(
        { block: { kind: "sign_in", items: [], links: [], provider: "google" } },
        { delta: "Sign in below to create it." },
        { done: true }
      ),
    })
  );
  await visit(page, "/");
  const panel = await openPanel(page);
  await panel.getByRole("textbox").fill("Create a company");
  await panel.locator("button[type=submit]").click();
  await expect(panel.getByRole("list").getByText("Sign in below to create it.")).toBeVisible();

  // A reload keeps the visitor's chat and the open panel.
  await page.reload();
  const again = page.getByRole("dialog");
  await expect(again.getByRole("list").getByText("Create a company")).toBeVisible();

  const sent = await assistantAnswers(page);
  const opened = context.waitForEvent("page");
  await again.getByTestId("sign-in-google").click();
  const popup = await opened;
  await popup.waitForLoadState();
  await popup.getByText(/add new account/i).click();
  await popup.locator("#email-input").fill(ownerEmail());
  await popup.locator("#display-name-input").fill("e2e owner");
  await popup.locator("#sign-in").click();
  await popup.waitForEvent("close");

  // Signed in, the panel is still open with the chat, without the sign-in card, and the next
  // message carries the chat.
  await expect(again.getByTestId("assistant-history")).toBeVisible();
  await expect(again.getByRole("list").getByText("Create a company")).toBeVisible();
  await expect(again.getByRole("list").getByText("Sign in below to create it.")).toBeVisible();
  await expect(again.locator('[data-testid^="sign-in-"]')).toHaveCount(0);

  // A reload before the first message keeps that chat (the user has no newer conversation).
  await page.route("**/api/assistant/conversations/active", (route) => route.fulfill({ status: 204 }));
  await page.reload();
  await expect(again.getByTestId("assistant-history")).toBeVisible({ timeout: 45_000 });
  await expect(again.getByRole("list").getByText("Create a company")).toBeVisible();
  await expect(again.getByRole("list").getByText("Sign in below to create it.")).toBeVisible();
  await expect(again.locator('[data-testid^="sign-in-"]')).toHaveCount(0);
  await again.getByRole("textbox").fill("Call it Acme");
  await again.locator("button[type=submit]").click();
  await expect(again.locator("strong", { hasText: "Ann" })).toBeVisible();
  expect(sent[0]).toMatchObject({
    message: "Call it Acme",
    earlier: [
      { role: "user", content: "Create a company" },
      { role: "assistant", content: "Sign in below to create it." },
    ],
  });
  await context.close();
});
