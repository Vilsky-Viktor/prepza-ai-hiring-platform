import { expect, test } from "@playwright/test";

import { pauseClock } from "./helpers/clock";
import { loaded } from "./helpers/waits";

// The home page's "see who's best" section: one frame playing the candidates list, its PDF
// downloaded and emailed, two candidates' pages shared to a chat, a note posted and the Slack
// channel testee posts to. On phones, what it does as cards.

// Steps the demo reaches, in order (frontend/src/config/reports-demo-steps.ts), each lasting
// over a second and a half: the PDF downloaded, then emailed; each candidate's summary in the
// chat; the note posted; Slack last.
const STEPS = ["downloaded", "sent", "summary0", "summary1", "posted", "slackScrolled"];

test("the reports demo reaches sharing, the notes and Slack, and the frame never moves", async ({
  page,
}) => {
  test.setTimeout(360_000);
  await page.clock.install();
  await page.goto("/");
  await loaded(page);
  // Time stands still from here on, moving only as the test runs it.
  await pauseClock(page);
  const section = page.locator("#reports");
  await section.scrollIntoViewIfNeeded();
  const demo = section.getByTestId("reports-demo");
  const frame = demo.getByTestId("demo-panel");
  const box = () =>
    frame.evaluate((element) => {
      const rect = element.getBoundingClientRect();

      return [rect.width, rect.height, rect.left, rect.top + window.scrollY].map(Math.round).join();
    });
  const boxes = new Set([await box()]);
  const seen = new Set<string>();

  // The clock runs a second and a half at a time, so none of those steps is passed unseen.
  await expect
    .poll(
      async () => {
        await page.clock.runFor(1_500);
        boxes.add(await box());
        seen.add((await demo.getAttribute("data-step"))!);

        return STEPS.filter((step) => seen.has(step));
      },
      { timeout: 300_000 },
    )
    .toEqual(STEPS);

  expect([...boxes]).toHaveLength(1);
});

test("on a phone what it does shows as three cards in place of the demo", { tag: "@phone-only" }, async ({
  page,
}) => {
  test.setTimeout(120_000);
  await page.goto("/");
  const section = page.locator("#reports");
  await section.scrollIntoViewIfNeeded();

  await expect(section.getByTestId("reports-demo")).toBeHidden();
  await expect(section.getByTestId("phone-steps").getByTestId("icon-card")).toHaveCount(3);
  await expect(section.getByTestId("notes")).toBeVisible();
});
