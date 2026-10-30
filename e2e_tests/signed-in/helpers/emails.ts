import type { Page } from "@playwright/test"

// The email settings' boxes, in their order (Settings > Emails, and an account found on the
// admin zone's emails tab): the digest, its five kinds (candidates who finished, undelivered
// invites, ATS candidates not invited, interviews ready, the team's new notes), then reminders,
// product updates and offers.
export const EMAIL_BOXES = {
  digest: 0,
  kinds: [1, 2, 3, 4, 5],
  undelivered: 2,
  ready: 4,
  notes: 5,
  reminders: 6,
  updates: 7,
  offers: 8,
  count: 9,
}

/** The email settings' boxes on the page. */
export function emailBoxes(page: Page) {
  return page.getByTestId("email-preferences").getByRole("checkbox")
}
