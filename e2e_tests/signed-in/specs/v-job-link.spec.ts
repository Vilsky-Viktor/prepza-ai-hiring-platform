import { expect, test } from "../fixtures";
import { api, createCompany, createInterview } from "../helpers/api";
import { inviteToken, joinedEmails } from "../helpers/db";
import { visit } from "../helpers/navigation";
import { shot } from "../helpers/screenshots";
import { ownerEmail, throwawayEmail } from "../helpers/users";

// Someone starts from a test's shareable link (a job ad) and is sent their own link by email.
// Their own link still works after the company turns the shareable link off.
test("a candidate starts from the job link and continues from their own link", async ({
  signInAs,
}) => {
  const owner = await signInAs(ownerEmail());
  const company = await createCompany(owner);
  const interviewId = await createInterview(owner, company.id);
  const { link_token: token } = await api<{ link_token: string }>(
    owner,
    "PUT",
    `/companies/interviews/${interviewId}/link`,
    { on: true },
  );

  const email = throwawayEmail("link-candidate");
  const candidate = await signInAs(email);
  // The page's only button starts the test.
  const start = candidate.getByRole("main").getByRole("button");
  await visit(candidate, `/apply/${token}`);
  await expect(start).toBeVisible();
  await shot(candidate, "job-link");
  await candidate.getByTestId("start-pledge").filter({ visible: true }).click();
  await start.click();
  await expect(candidate).toHaveURL(/\/sessions\//);
  await expect.poll(() => joinedEmails(email)).toBe(1);

  // The company takes the link down; the emailed link still continues the interview.
  await api(owner, "PUT", `/companies/interviews/${interviewId}/link`, {
    on: false,
  });
  await visit(candidate, `/invite/${await inviteToken(email)}`);
  // Continuing: pledged already, so no box to tick.
  await expect(candidate.getByTestId("start-pledge")).toHaveCount(0);
  await start.click();
  await expect(candidate).toHaveURL(/\/sessions\//);
  // Starting again sends no second email.
  expect(await joinedEmails(email)).toBe(1);
});
