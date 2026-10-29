import { expect, test } from "../fixtures";
import {
  createCompany,
  createInterview,
  inviteCandidate,
} from "../helpers/api";
import { inviteToken } from "../helpers/db";
import { openDialog, visit } from "../helpers/navigation";
import { shot } from "../helpers/screenshots";
import { answered } from "../helpers/session";
import { ownerEmail, throwawayEmail } from "../helpers/users";
import { MIN_QUESTION_SECONDS } from "../constants";

// A candidate takes an interview from their invite link: picks, changes the pick, goes on, lets a
// question's time run out, and finishes.
test("candidate takes the interview from the invite link", async ({
  signInAs,
}) => {
  const owner = await signInAs(ownerEmail());
  const company = await createCompany(owner);
  const interviewId = await createInterview(owner, company.id);
  const email = throwawayEmail("candidate");
  await inviteCandidate(owner, interviewId, email);

  const candidate = await signInAs(email);
  const invitePath = `/invite/${await inviteToken(email)}`;
  await visit(candidate, invitePath);
  await expect(candidate.getByText(company.name).first()).toBeVisible();
  await shot(candidate, "invite");
  // The invitation's one button starts it, once the candidate pledges to answer on their own.
  await candidate.getByTestId("start-pledge").click();
  await candidate.getByRole("main").getByRole("button").click();
  await expect(candidate).toHaveURL(/\/sessions\//);

  // The pick can change until Next: one option marked at a time.
  const question = candidate.locator("[role=heading]").first();
  // The answer's options, a list beside the question (the rating's buttons are pressed too).
  const options = candidate.getByRole("main").locator("li > button[aria-pressed]");
  await expect(options.first()).toBeVisible();
  await shot(candidate, "question");
  await options.nth(0).click();
  await expect(options.nth(0)).toHaveAttribute("aria-pressed", "true");
  await options.nth(1).click();
  await expect(options.nth(1)).toHaveAttribute("aria-pressed", "true");
  await expect(options.nth(0)).toHaveAttribute("aria-pressed", "false");
  await shot(candidate, "pick-changed");

  // A picked question can be reported (the flag icon, named for screen readers); its reason
  // comes from the site's menu, not the browser's, and sending needs one.
  await openDialog(
    candidate,
    candidate.getByRole("button", { name: "Report question" }),
  );
  const report = candidate.getByRole("dialog");
  const reason = report.getByRole("button").first();
  const send = report.locator('button[type="submit"]');
  const unpicked = await reason.textContent();
  await expect(send).toBeDisabled();
  await reason.click();
  await expect(candidate.locator("select")).toHaveCount(0);
  await shot(candidate, "report-reasons");
  await candidate.getByRole("menu").getByRole("menuitemradio").first().click();
  await expect(candidate.getByRole("menu")).toHaveCount(0);
  await expect(reason).not.toHaveText(unpicked ?? "");
  await expect(send).toBeEnabled();
  await shot(candidate, "report-reason-picked");
  // Cancel, beside Send: nothing is reported.
  await report.getByRole("button").nth(1).click();
  await expect(report).toHaveCount(0);
  const first = await question.textContent();
  // The footer: Next on the right once something is picked.
  const footer = candidate.locator("[data-round-footer]");
  await footer.getByRole("button").last().click();
  await expect(question).not.toHaveText(first ?? "");
  await expect.poll(() => answered(candidate)).toBe("1");

  // No pick: the question's clock runs out and the next one opens by itself.
  const second = await question.textContent();
  await expect(candidate.getByRole("timer")).toBeVisible();
  await shot(candidate, "timer");
  await expect(question).not.toHaveText(second ?? "", {
    timeout: (MIN_QUESTION_SECONDS + 10) * 1000,
  });
  await expect.poll(() => answered(candidate)).toBe("2");
  await shot(candidate, "after-timeout");

  // Finish asks first; its confirmation is the dialog's last button.
  await candidate.getByTestId("finish-interview").click();
  await expect(candidate.getByRole("dialog")).toBeVisible();
  await shot(candidate, "finish-dialog");
  await candidate.getByRole("dialog").getByRole("button").last().click();
  // Finished: the interview's title, and no question or footer left.
  await expect(candidate.getByRole("heading", { level: 1 })).toBeVisible();
  await expect(footer).toHaveCount(0);
  await expect(candidate.locator("button[aria-pressed]")).toHaveCount(0);
  await shot(candidate, "done");
  // A company's interview shows the company only: no prepza header or footer, finished too.
  await expect(candidate.locator("header, footer")).toHaveCount(0);

  // The invite link now says the interview is finished, in an info card instead of the start.
  await visit(candidate, invitePath);
  await expect(candidate.getByText(company.name).first()).toBeVisible();
  await expect(candidate.getByRole("status")).toBeVisible();
  await expect(candidate.getByRole("main").getByRole("button")).toHaveCount(0);
  await shot(candidate, "invite-finished");

  // The company sees them finished.
  await visit(
    owner,
    `/companies/${company.id}/interviews/${interviewId}?tab=candidates`,
  );
  await expect(owner.getByText(email, { exact: true }).first()).toBeVisible();
  await shot(owner, "owner-candidates");

  // Their report lists the questions they answered, without numbers.
  await owner.getByText(email, { exact: true }).first().click();
  await expect(owner.getByText(first ?? "").first()).toBeVisible();
  await expect(owner.getByText(/^\d+\.$/)).toHaveCount(0);
  // A finished candidate's invite isn't sent again.
  await expect(owner.getByTestId("resend-invite")).toHaveCount(0);
  await shot(owner, "owner-report");
});

// A visitor who isn't signed in sees what the invitation is for and a button to sign in, not the
// invited email; someone signed in with another email sees why they can't start, in a warning.
test("an invitation asks a visitor to sign in, and warns another email", async ({
  browser,
  signInAs,
}) => {
  const owner = await signInAs(ownerEmail());
  const company = await createCompany(owner);
  const interviewId = await createInterview(owner, company.id);
  const email = throwawayEmail("candidate");
  await inviteCandidate(owner, interviewId, email);
  const path = `/invite/${await inviteToken(email)}`;

  const context = await browser.newContext();

  try {
    const visitor = await context.newPage();
    await visit(visitor, path);
    await expect(visitor.getByText(company.name).first()).toBeVisible();
    await expect(visitor.getByText(email)).toHaveCount(0);
    await shot(visitor, "invite-signed-out");
    // Its one button signs in rather than starting.
    await visitor.getByRole("main").getByRole("button").click();
    await expect(visitor.getByRole("dialog")).toBeVisible();
    await expect(visitor).toHaveURL(new RegExp(`${path}$`));
  } finally {
    await context.close();
  }

  const other = await signInAs(throwawayEmail("other"));
  await visit(other, path);
  await expect(other.getByText(company.name).first()).toBeVisible();
  await expect(other.getByRole("status")).toContainText(
    "The email does not match. Sign in with the invitation email to start.",
  );
  await expect(other.getByRole("main").getByRole("button")).toHaveCount(0);
  await shot(other, "invite-other-email");
});

// Until the candidate starts, their page has the invite link to copy, in case the email didn't
// reach them.
test("a candidate's page has their invite link to copy", async ({
  signInAs,
}) => {
  const owner = await signInAs(ownerEmail());
  const company = await createCompany(owner);
  const interviewId = await createInterview(owner, company.id);
  const email = throwawayEmail("candidate");
  await inviteCandidate(owner, interviewId, email);

  await visit(
    owner,
    `/companies/${company.id}/interviews/${interviewId}?tab=candidates`,
  );
  await owner.getByText(email, { exact: true }).first().click();
  await expect(owner.getByRole("main").getByRole("textbox")).toHaveValue(
    new RegExp(`/invite/${await inviteToken(email)}$`),
  );
  await expect(owner.getByTestId("resend-invite")).toBeVisible();
  await shot(owner, "candidate-invite-link");
});
