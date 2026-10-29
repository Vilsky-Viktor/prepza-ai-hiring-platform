import { expect, test } from "../fixtures";
import {
  createCompany,
  createInterview,
  inviteCandidate,
} from "../helpers/api";
import { setInvitedAt } from "../helpers/db";
import { ownerEmail, throwawayEmail } from "../helpers/users";

// Dates are the visitor's own: a candidate invited at 2:00 UTC on the 15th was invited on the
// 14th for someone in New York, however the server renders the page.
test("a date shows in the visitor's time zone", async ({
  browser,
  signInAs,
}) => {
  const owner = await signInAs(ownerEmail());
  const company = await createCompany(owner);
  const interviewId = await createInterview(owner, company.id);
  const email = throwawayEmail("late-candidate");
  await inviteCandidate(owner, interviewId, email);
  await setInvitedAt(email, "2026-10-15T02:00:00Z");

  // The same signed-in person, in New York.
  const newYork = await browser.newContext({
    timezoneId: "America/New_York",
    storageState: await owner.context().storageState({ indexedDB: true }),
  });
  const page = await newYork.newPage();

  try {
    await page.goto(
      `/companies/${company.id}/interviews/${interviewId}?tab=candidates`,
    );
    const row = page
      .getByRole("main")
      .getByText(email)
      .locator("xpath=ancestor::li[1]");
    await expect(row.getByText("Oct 14, 2026").filter({ visible: true })).toBeVisible({
      timeout: 60_000,
    });
  } finally {
    await newYork.close();
  }
});
