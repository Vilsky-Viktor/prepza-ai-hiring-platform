import { expect, type Locator, type Page, test } from "@playwright/test";

// Signed out, "ask agent" opens the assistant with FAQ answers only: the welcome for visitors,
// an answer from the help chat (stubbed here: no OpenAI in tests), and a sign-in card when the
// visitor asks to sign in. No history, company or voice.

/** The help chat answering with these server-sent events. */
async function helpAnswers(page: Page, events: object[]) {
  await page.route("**/api/rounds/help/chat", (route) =>
    route.fulfill({
      contentType: "text/event-stream",
      body: [...events, { done: true }].map((event) => `data: ${JSON.stringify(event)}\n\n`).join(""),
    })
  );
}

/** The header's "ask agent". */
function askAgent(page: Page) {
  return page.getByRole("banner").locator("[data-assistant-toggle]");
}

async function openPanel(page: Page) {
  await page.goto("/");
  await askAgent(page).click();
  const panel = page.getByRole("dialog");
  await expect(panel).toBeVisible();

  return panel;
}

/** The questions the empty panel offers to tap. */
function welcomeQuestions(panel: Locator) {
  return panel.getByRole("list").getByRole("button");
}

test("a visitor asks the assistant about prepza", async ({ page }) => {
  await helpAnswers(page, [{ delta: "Each candidate costs " }, { delta: "**$1–3**." }]);
  const panel = await openPanel(page);

  // Questions to tap, and no history or voice (both toggle buttons).
  await expect(welcomeQuestions(panel).first()).toBeVisible();
  await expect(panel.locator("button[aria-pressed]")).toHaveCount(0);

  // Open, the input is ready to type in, but not on a touch phone, where the keyboard would
  // cover the welcome.
  const field = panel.getByRole("textbox");

  if (test.info().project.name === "phone") {
    await expect(field).not.toBeFocused();
  } else {
    await expect(field).toBeFocused();
  }

  // A welcome question is sent as the message; the answer's markdown is rendered.
  const question = (await welcomeQuestions(panel).first().textContent())!;
  await welcomeQuestions(panel).first().click();
  await expect(panel.getByRole("list").getByText(question)).toBeVisible();
  await expect(panel.locator("strong", { hasText: "$1–3" })).toBeVisible();

  if (test.info().project.name !== "phone") {
    await expect(field).toBeFocused();
  }

  // The wheel over the panel never scrolls the page behind it; over the page, it does.
  if (test.info().project.name !== "phone") {
    const before = await page.evaluate(() => window.scrollY);
    const box = (await panel.boundingBox())!;
    await page.mouse.move(box.x + box.width / 2, box.y + 40);
    await page.mouse.wheel(0, 600);
    await page.mouse.move(box.x + box.width / 2, box.y + box.height / 2);
    await page.mouse.wheel(0, 600);
    await page.waitForTimeout(300);
    expect(await page.evaluate(() => window.scrollY)).toBe(before);
    await page.mouse.move(100, 400);
    await page.mouse.wheel(0, 600);
    await expect.poll(() => page.evaluate(() => window.scrollY)).toBeGreaterThan(before);
  }

  // A click beside the panel closes it on wider screens; reopened, the chat is still there.
  if (test.info().project.name !== "phone") {
    await page.mouse.click(100, 500);
    await expect(panel).toHaveCount(0);
    await askAgent(page).click();
    await expect(panel.locator("strong", { hasText: "$1–3" })).toBeVisible();
  }

  // New chat starts over with the welcome; Close closes the panel.
  await panel.getByTestId("assistant-new-chat").click();
  await expect(welcomeQuestions(panel).first()).toBeVisible();
  await expect(panel.locator("strong", { hasText: "$1–3" })).toHaveCount(0);
  await panel.getByTestId("assistant-close").click();
  await expect(panel).toHaveCount(0);
});

test("Enter sends a message and ⌘/Ctrl + Enter adds a new line", async ({ page }) => {
  await helpAnswers(page, [{ delta: "Yes." }]);
  const panel = await openPanel(page);
  const field = panel.getByRole("textbox");

  await field.fill("First line");
  await field.press("ControlOrMeta+Enter");
  await field.pressSequentially("second line");

  // A new line, and nothing sent yet.
  await expect(field).toHaveValue("First line\nsecond line");
  await expect(welcomeQuestions(panel).first()).toBeVisible();

  await field.press("Enter");
  await expect(panel.getByRole("list").getByText(/^First line\s+second line$/)).toBeVisible();
  await expect(field).toHaveValue("");
});

test("a visitor asking to sign in gets the sign-in card, their way first", async ({ page }) => {
  await helpAnswers(page, [
    { block: { kind: "sign_in", items: [], links: [], provider: "github" } },
    { delta: "Sign in below with GitHub." },
  ]);
  const panel = await openPanel(page);
  await panel.getByRole("textbox").fill("sign me in with github");
  await panel.locator('button[type="submit"]').click();

  await expect(panel.getByRole("list").getByText("Sign in below with GitHub.")).toBeVisible();
  const ways = panel.locator('[data-testid^="sign-in-"]');
  await expect(ways).toHaveCount(3);
  await expect(ways.first()).toHaveAttribute("data-testid", "sign-in-github");
});

test("a reply goes back with its signature, and the next question isn't checked again", async ({ page }) => {
  const sent: { body: { messages: object[] }; checked: boolean }[] = [];
  await page.route("**/api/rounds/help/chat", (route) => {
    const request = route.request();
    sent.push({ body: request.postDataJSON(), checked: "x-human-check" in request.headers() });
    const events = [{ delta: "Paste it." }, { done: true, signature: `sig-${sent.length}` }];

    return route.fulfill({
      contentType: "text/event-stream",
      body: events.map((event) => `data: ${JSON.stringify(event)}\n\n`).join(""),
    });
  });
  const panel = await openPanel(page);
  await panel.getByRole("textbox").fill("How do I start?");
  await panel.locator('button[type="submit"]').click();
  await expect(panel.getByRole("list").getByText("Paste it.")).toBeVisible();
  await panel.getByRole("textbox").fill("And then?");
  await panel.locator('button[type="submit"]').click();
  await expect.poll(() => sent.length).toBe(2);

  expect(sent[1].body.messages).toEqual([
    { role: "user", content: "How do I start?" },
    { role: "assistant", content: "Paste it.", signature: "sig-1" },
    { role: "user", content: "And then?" },
  ]);
  expect(sent.map((request) => request.checked)).toEqual([true, false]);
});

test("a failed answer shows its error and Try again asks again", async ({ page }) => {
  let calls = 0;
  await page.route("**/api/rounds/help/chat", (route) => {
    calls += 1;

    return calls === 1
      ? route.fulfill({ status: 503, json: { detail: "Paused for now." } })
      : route.fulfill({ contentType: "text/event-stream", body: 'data: {"delta":"Back."}\n\n' });
  });
  const panel = await openPanel(page);
  await panel.getByRole("textbox").fill("Hi");
  await panel.locator('button[type="submit"]').click();
  await expect(panel.getByRole("list").getByText("Paused for now.")).toBeVisible();

  // The failed answer's one button asks again.
  await panel.getByRole("list").getByRole("button").click();
  await expect(panel.getByRole("list").getByText("Back.")).toBeVisible();
  await expect(panel.getByRole("list").getByText("Paused for now.")).toHaveCount(0);
});

test("a reload in the middle of a visitor's chat brings it back", async ({ page }) => {
  await helpAnswers(page, [{ delta: "A hiring test." }]);
  const panel = await openPanel(page);
  const question = (await welcomeQuestions(panel).first().textContent())!;
  await welcomeQuestions(panel).first().click();
  await expect(panel.getByRole("list").getByText("A hiring test.")).toBeVisible();

  await page.reload();
  const again = page.getByRole("dialog");
  await expect(again.getByRole("list").getByText(question)).toBeVisible();
  await expect(again.getByRole("list").getByText("A hiring test.")).toBeVisible();

  // A chat older than the service's window (GET /config) isn't brought back.
  await page.evaluate(() => {
    const kept = JSON.parse(sessionStorage.getItem("prepza:assistant:visitor") ?? "{}");
    kept.lastAt = new Date(Date.now() - 31 * 60_000).toISOString();
    sessionStorage.setItem("prepza:assistant:visitor", JSON.stringify(kept));
  });
  await page.reload();
  await expect(askAgent(page)).toBeVisible();
  await expect(again).toHaveCount(0);

  // Opened, it's a new chat; closed, it stays closed after a reload.
  await askAgent(page).click();
  await expect(welcomeQuestions(again).first()).toBeVisible();
  await expect(again.getByRole("list").getByText("A hiring test.")).toHaveCount(0);
  await again.getByTestId("assistant-close").click();
  await page.reload();
  await expect(askAgent(page)).toBeVisible();
  await expect(again).toHaveCount(0);
});

// Popups slide and fade in and out (components/ui/dialog.tsx): each closes fully, with nothing
// left behind, and gives the focus back to what opened it; reduced motion still opens and
// closes them.
for (const reducedMotion of ["no-preference", "reduce"] as const) {
  test(`the panel and a dialog open and close fully (${reducedMotion} motion)`, async ({ page }) => {
    await page.emulateMedia({ reducedMotion });
    await page.goto("/");
    const toggle = askAgent(page);
    await toggle.click();
    const panel = page.getByRole("dialog");
    await expect(panel).toBeVisible();
    await expect(panel).toBeInViewport({ ratio: 1 });

    await panel.getByTestId("assistant-close").click();
    await expect(page.locator('[data-slot="dialog-content"]')).toHaveCount(0);
    await expect(toggle).toBeFocused();

    // Signed out, the header's Sign in opens the sign-in dialog, over a dimmed page.
    const signIn = page.getByRole("banner").getByTestId("header-sign-in");
    await signIn.click();
    const dialog = page.getByRole("dialog");
    await expect(dialog).toBeVisible();
    await expect(page.locator('[data-slot="dialog-overlay"]')).toBeVisible();

    await page.keyboard.press("Escape");
    await expect(page.locator('[data-slot="dialog-content"]')).toHaveCount(0);
    await expect(page.locator('[data-slot="dialog-overlay"]')).toHaveCount(0);
    await expect(signIn).toBeFocused();
  });
}
