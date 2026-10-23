import { expect, test, type Locator, type Page } from "@playwright/test";

import { loaded } from "./helpers/waits";

// The home page's "trust, quality and compliance" section: five steps of one size spaced evenly
// round an ellipse, a question running round them and lighting each in turn, the AI chip with light running out of it through the net in
// the middle; with reduced motion all of it still. Under it, four columns, one linking to the
// documents.

async function openTrust(page: Page) {
  await page.goto("/");
  await loaded(page);
  const section = page.locator("#trust");
  await section.scrollIntoViewIfNeeded();

  return section;
}

async function centre(element: Locator) {
  const box = (await element.boundingBox())!;

  return { x: box.x + box.width / 2, y: box.y + box.height / 2, ...box };
}

// The lit step's position among the steps, once one is lit, running the paused clock meanwhile.
async function litStep(page: Page, steps: Locator, other?: number) {
  let lit = -1;
  await expect
    .poll(
      async () => {
        await page.clock.runFor(250);
        const states = await steps.evaluateAll((all) =>
          all.map((step) => step.hasAttribute("data-lit")),
        );
        lit = states.filter(Boolean).length === 1 ? states.indexOf(true) : -1;

        return lit !== -1 && lit !== other;
      },
      { timeout: 60_000 },
    )
    .toBe(true);

  return lit;
}

test("the steps light up one at a time, in order round the ring", async ({
  page,
}) => {
  test.setTimeout(120_000);
  await page.clock.install();
  const section = await openTrust(page);
  const now = await page.evaluate(() => Date.now());
  // A few seconds ahead, so a slow page never has the clock past it already.
  await page.clock.pauseAt(now + 5_000);
  const steps = section.getByTestId("quality-step");
  await expect(steps).toHaveCount(5);

  const first = await litStep(page, steps);
  const next = await litStep(page, steps, first);
  expect(next).toBe((first + 1) % 5);
  await expect(section.getByTestId("ai-chip")).toBeVisible();
  await expect(section.getByTestId("net-wave")).toHaveCount(1);
});

test("the steps are one size, mirrored round the middle, and lighting keeps the size", async ({
  page,
}) => {
  test.setTimeout(120_000);
  await page.clock.install();
  const section = await openTrust(page);
  const now = await page.evaluate(() => Date.now());
  // A few seconds ahead, so a slow page never has the clock past it already.
  await page.clock.pauseAt(now + 5_000);
  const steps = section.getByTestId("quality-step");
  const before = await Promise.all((await steps.all()).map(centre));
  const [top, right, lowerRight, lowerLeft, left] = before;
  const middle = (left.x + right.x) / 2;

  for (const step of before) {
    expect(step.width).toBeCloseTo(top.width, 0);
    expect(step.height).toBeCloseTo(top.height, 0);
  }

  expect(top.x).toBeCloseTo(middle, 0);
  expect(left.y).toBeCloseTo(right.y, 0);
  expect(lowerLeft.y).toBeCloseTo(lowerRight.y, 0);
  expect(middle - lowerLeft.x).toBeCloseTo(lowerRight.x - middle, 0);

  const lit = await litStep(page, steps);
  const shown = await centre(steps.nth(lit));
  expect([shown.width, shown.height]).toEqual([
    before[lit].width,
    before[lit].height,
  ]);
});

test("only one question travels the ring at a time", async ({ page }) => {
  test.setTimeout(120_000);
  const section = await openTrust(page);
  await expect(section.getByTestId("quality-step")).toHaveCount(5);

  // The most travellers shown at once over a few seconds of the loop playing, sampled in the
  // page (its SMIL animations run on their own clock, not Playwright's).
  const most = await section.evaluate(
    (element) =>
      new Promise<number>((resolve) => {
        let peak = 0;
        const sample = window.setInterval(() => {
          const shown = [
            ...element.querySelectorAll('[data-testid="wire-traveller"]'),
          ].filter((traveller) => Number(getComputedStyle(traveller).opacity) > 0.05);
          peak = Math.max(peak, shown.length);
        }, 50);
        window.setTimeout(() => {
          window.clearInterval(sample);
          resolve(peak);
        }, 6_000);
      }),
  );

  expect(most).toBeLessThanOrEqual(1);
});

test("the light runs through the whole net, left of the chip as well as right", async ({
  page,
}) => {
  test.setTimeout(120_000);
  const section = await openTrust(page);
  await expect(section.getByTestId("net-wave")).toHaveCount(1);
  const chip = await centre(section.getByTestId("ai-chip"));
  const step = await centre(section.getByTestId("quality-step").first());

  // The net between the chip and the steps on each side, at the chip's height.
  const patch = (side: -1 | 1) => ({
    x: chip.x + side * (chip.width / 2 + step.width / 4) - step.width / 8,
    y: chip.y - step.height / 4,
    width: step.width / 4,
    height: step.height / 2,
  });

  // The waves' SMIL clock held still: at the start no ring shows; two seconds in, the first ring
  // has spread past the chip on every side.
  const at = async (seconds: number) => {
    await section.locator('svg:has([data-testid="net-wave"])').evaluate((svg: SVGSVGElement, time) => {
      svg.pauseAnimations();
      svg.setCurrentTime(time);
    }, seconds);

    return Promise.all(
      ([-1, 1] as const).map((side) =>
        page.screenshot({ clip: patch(side), animations: "disabled" }),
      ),
    );
  };
  const dark = await at(0);
  const lit = await at(2);

  expect(lit[0].equals(dark[0])).toBe(false);
  expect(lit[1].equals(dark[1])).toBe(false);
});

test("with reduced motion, no step lights up", async ({
  page,
}) => {
  test.setTimeout(120_000);
  await page.emulateMedia({ reducedMotion: "reduce" });
  await page.clock.install();
  const section = await openTrust(page);
  await page.clock.runFor(10_000);

  await expect(section.getByTestId("quality-step")).toHaveCount(5);
  await expect(section.locator("[data-lit]")).toHaveCount(0);
  await expect(section.getByTestId("net-wave")).toHaveCount(0);
});

test("the four columns show, one linking to the documents", async ({
  page,
}) => {
  test.setTimeout(120_000);
  const section = await openTrust(page);
  const columns = section.getByRole("list").last().getByRole("listitem");
  await expect(columns).toHaveCount(4);

  // Side by side on a desktop, their titles start on one line.
  if (test.info().project.name !== "phone") {
    const tops = await Promise.all(
      (await columns.getByRole("heading").all()).map(
        async (title) => (await title.boundingBox())!.y,
      ),
    );

    for (const top of tops) {
      expect(top).toBeCloseTo(tops[0], 0);
    }
  }

  await columns.getByRole("link").click();
  // The local dev server compiles the documents on first open.
  await expect(page).toHaveURL(/\/documents$/, { timeout: 60_000 });
});
