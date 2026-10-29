import { type Locator, type Page } from "@playwright/test";

import { expect, test } from "../fixtures";
import {
  api,
  createCompany,
  createInterview,
  deleteOwnCompanies,
  finishOneAnswer,
  inviteCandidate,
  templatesBySize,
} from "../helpers/api";
import { box, PHONE, settled } from "../helpers/layout";
import { integrationRow, visit } from "../helpers/navigation";
import { ownerEmail, throwawayEmail } from "../helpers/users";

// How the signed-in pages fit a phone: lists and panels out to the screen's edges, actions on
// their own lines, dialogs across the screen with their buttons side by side, a long email
// breaking before its @, and timed questions with nothing around them.

// The page's visible width, without the scrollbar desktop Chrome draws (phones draw none): also
// on a company's interview pages, which have no header to measure.
async function pageWidth(page: Page) {
  return page.evaluate(() => document.body.getBoundingClientRect().width);
}

// Out to both edges of the screen.
async function expectEdgeToEdge(page: Page, locator: Locator) {
  const found = await box(locator);
  expect(found.left).toBeLessThanOrEqual(0);
  expect(found.left + found.width).toBeGreaterThanOrEqual(
    await pageWidth(page),
  );
}

test("a company's pages on a phone", async ({ signInAs }) => {
  test.setTimeout(300_000);
  // An owner's own inbox: a first company's welcome credits pay for the candidate invited below.
  const user = await signInAs(ownerEmail());
  const company = await createCompany(user);
  const interview = await createInterview(user, company.id);
  await api(user, "POST", `/companies/members?company_id=${company.id}`, {
    email: throwawayEmail("phone-member"),
    role: "admin",
  });
  await user.setViewportSize(PHONE);

  try {
    // The companies list: "new company" at full width under the title, cards across the screen.
    await visit(user, "/companies");
    const width = await pageWidth(user);
    const title = user.getByRole("main").getByRole("heading", { level: 1 });
    const create = user.getByTestId("new-company");
    expect((await box(create)).top).toBeGreaterThan((await box(title)).bottom);
    expect((await box(create)).width).toBeGreaterThan(width - 60);
    await expectEdgeToEdge(
      user,
      user.getByRole("main").getByRole("listitem").first(),
    );

    // A dialog spans the screen, its two buttons (Cancel, Create) side by side, as tall and in
    // the same font.
    await create.click();
    const dialog = user.getByRole("dialog");
    await settled(dialog);
    expect((await box(dialog)).left).toBe(0);
    const footer = dialog.locator("[data-slot=dialog-footer]").getByRole("button");
    const cancel = await box(footer.first());
    const submit = await box(footer.last());
    expect(submit.top).toBe(cancel.top);
    expect(submit.width).toBe(cancel.width);
    await expect(footer.last()).toHaveCSS(
      "font-size",
      "16px",
    );
    await user.keyboard.press("Escape");

    // A company's interviews: the back arrow above the name, "new interview" under it, and
    // rows with only the title and date.
    await visit(user, `/companies/${company.id}/interviews`);
    const back = await box(user.locator('main a[href="/companies"]'));
    const name = await box(user.getByRole("heading", { level: 1 }));
    expect(back.bottom).toBeLessThanOrEqual(name.top + 4);
    const newInterview = user.locator(
      `main a[href="/companies/${company.id}/interviews/new"]`,
    );
    expect((await box(newInterview)).top).toBeGreaterThan(name.bottom);
    expect((await box(newInterview)).width).toBeGreaterThan(width - 60);
    const row = user.locator("main .divide-y > *").first();
    await expect(row.locator('a[href$="/try"]')).toBeHidden();
    await expect(row.locator("[data-slot=interview-stats]")).toBeHidden();

    // A template: "use template" under its title, across the page, however long the title.
    const [template] = await templatesBySize(user);
    await visit(user, `/companies/${company.id}/templates/${template.id}`);
    const templateTitle = await box(user.getByRole("heading", { level: 1 }));
    const use = await box(user.getByTestId("use-template"));
    expect(use.top).toBeGreaterThan(templateTitle.bottom);
    expect(use.width).toBeGreaterThan(width - 60);

    // The team: each member's role on the line under their email.
    await visit(user, `/companies/${company.id}/members`);
    const member = user.locator("main .divide-y > *").first();
    const email = await box(member.getByText(/@/).first());
    const role = await box(member.locator("[data-slot=badge]").first());
    expect(role.top).toBeGreaterThanOrEqual(email.bottom);

    // The last tab, past the screen's edge, is scrolled into view in its row when it's open
    // (once the page has hydrated, so it's polled).
    await visit(user, `/companies/${company.id}/referrals`);
    const shown = () =>
      user.evaluate((id) => {
        const tab = document.querySelector(`main nav a[href="/companies/${id}/referrals"]`);
        const row = tab?.closest("nav")?.parentElement;
        const [inner, outer] = [tab, row].map((element) => element!.getBoundingClientRect());

        return inner.left >= outer.left - 1 && inner.right <= outer.right + 1;
      }, company.id);
    await expect.poll(shown).toBe(true);

    // Integrations: a small logo beside the name, the buttons on the line under both.
    await visit(user, `/companies/${company.id}/integrations`);
    const slack = integrationRow(user, "/slack");
    // The link's two parts: the logo, then the name and its text.
    const slackName = await box(slack.getByRole("link").locator("> span").nth(1));
    const logo = await box(slack.getByRole("link").locator("span").first());
    const instructions = await box(slack.getByTestId("instructions"));
    expect(logo.width).toBe(48);
    expect(slackName.left).toBeGreaterThan(logo.right);
    expect(instructions.top).toBeGreaterThan(logo.bottom);
    expect(instructions.left).toBeLessThan(logo.right);

    // A finished candidate's page: a long email has no spaces to wrap at, so it breaks before the
    // @ rather than running off the screen, and the note under the results spans the screen.
    const candidate = throwawayEmail("averyveryverylongcandidateaddress");
    await inviteCandidate(user, interview, candidate);
    await finishOneAnswer(await signInAs(candidate), candidate);
    await visit(user, `/companies/${company.id}/interviews/${interview}?tab=candidates`);
    await user.getByRole("link").filter({ hasText: "averyveryverylong" }).click();
    await expect(user.getByTestId("human-review").filter({ visible: true })).toBeVisible();
    expect(await user.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(
      PHONE.width,
    );
  } finally {
    await deleteOwnCompanies(user);
  }
});

// While questions run against the clock there's only the question: no header, footer or
// "ask Mira"; nor on a member's preview of its invitation before. A company's interview,
// finished, shows the company only, with its button back to the interviews.
test("timed questions on their own, with nothing around them", async ({
  signInAs,
}) => {
  test.setTimeout(300_000);
  const user = await signInAs(throwawayEmail("timed"));
  const company = await createCompany(user);
  const interview = await createInterview(user, company.id);

  try {
    // The preview shows what candidates see: no header or footer from its invitation on.
    await visit(user, `/companies/${company.id}/interviews/${interview}/try`);
    // The visible ones: the page can hold a hidden copy of its parts while they stream in.
    const start = user.getByTestId("accept-start").filter({ visible: true });
    await expect(start).toBeVisible();
    await expect(user.getByRole("banner")).toHaveCount(0);
    await expect(user.getByRole("contentinfo")).toHaveCount(0);
    await user.getByTestId("start-pledge").filter({ visible: true }).click();
    await start.click();
    await expect(user).toHaveURL(/\/sessions\//, { timeout: 90_000 });
    const finish = user.getByTestId("finish-interview");
    await expect(finish).toBeVisible();
    await expect(user.getByRole("banner")).toHaveCount(0);
    await expect(user.getByRole("contentinfo")).toHaveCount(0);
    await expect(user.locator("[data-assistant-toggle]")).toHaveCount(0);

    // Once it's finished (the dialog's last button confirms), still none: a company's
    // interview shows the company only, with its way back to the interviews.
    await finish.click();
    await user.getByRole("dialog").getByRole("button").last().click();
    await expect(
      user.locator(`main a[href="/companies/${company.id}/interviews"]`),
    ).toBeVisible({ timeout: 60_000 });
    await expect(user.getByRole("banner")).toHaveCount(0);
    await expect(user.getByRole("contentinfo")).toHaveCount(0);
  } finally {
    await deleteOwnCompanies(user);
  }
});

// On a phone the invitation's rules come before "accept & start", out to the screen's edges, and
// the start button is the start pages' big size.
test("an invitation's rules come before its start on a phone", async ({
  signInAs,
}) => {
  test.setTimeout(300_000);
  const user = await signInAs(throwawayEmail("rules"));
  const company = await createCompany(user);
  const interview = await createInterview(user, company.id);
  await user.setViewportSize(PHONE);

  try {
    await visit(user, `/companies/${company.id}/interviews/${interview}/try`);
    const rules = user.getByTestId("invite-rules");
    const start = await box(user.getByTestId("accept-start"));
    expect(start.top).toBeGreaterThan((await box(rules)).bottom);
    expect(start.height).toBe(56);
    await expectEdgeToEdge(user, rules);
  } finally {
    await deleteOwnCompanies(user);
  }
});
