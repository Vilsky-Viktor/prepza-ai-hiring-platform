import { expect, test, type Page } from "@playwright/test";

import { loaded } from "./helpers/waits";

// The home page's "invite candidates" picture: every way in and Slack around the interview, each
// joined to it by a wire, and the link to the developer docs above it.

const WAYS_IN = ["ats", "email", "file", "link", "api", "sdk", "agent", "apps"];

async function openPicture(page: Page) {
  await page.goto("/");
  await loaded(page);
  const section = page.locator("#invite");
  await section.scrollIntoViewIfNeeded();

  return section;
}

test("every way in and Slack are joined to the interview by a wire", async ({ page }) => {
  // The local dev server compiles the home page on first open.
  test.setTimeout(120_000);
  const section = await openPicture(page);
  const cards = section.getByTestId("invite-card");
  await expect(cards).toHaveCount(WAYS_IN.length + 1);
  expect(await cards.evaluateAll((all) => all.map((card) => card.dataset.mark))).toEqual([
    ...WAYS_IN,
    "slack",
  ]);
  // The wires themselves, not the travellers' icons drawn on them.
  const wires = section.locator("svg > g > path");
  await expect(wires).toHaveCount(WAYS_IN.length + 1);

  // Each wire starts on a card and ends on the interview's card, Slack's the other way round:
  // both ends within a card's laid-out box, so none is drawn from a card that isn't there.
  const ends = await section.evaluate((element) => {
    const box = (part: HTMLElement) => ({
      left: part.offsetLeft,
      top: part.offsetTop,
      right: part.offsetLeft + part.offsetWidth,
      bottom: part.offsetTop + part.offsetHeight,
    });
    const interview = box(element.querySelector<HTMLElement>("[data-testid=invite-interview]")!);
    const cards = [...element.querySelectorAll<HTMLElement>("[data-testid=invite-card]")].map(
      (card) => ({ mark: card.dataset.mark!, ...box(card) }),
    );
    const within = (b: typeof interview, x: number, y: number) =>
      x >= b.left - 1 && x <= b.right + 1 && y >= b.top - 1 && y <= b.bottom + 1;

    return [...element.querySelectorAll("svg > g > path")].map((path) => {
      const numbers = path.getAttribute("d")!.match(/-?[\d.]+(?:e-?\d+)?/g)!.map(Number);
      const [x1, y1] = numbers;
      const [x2, y2] = numbers.slice(-2);
      const from = cards.find((card) => within(card, x1, y1));
      const to = cards.find((card) => within(card, x2, y2));

      return {
        from: from?.mark ?? (within(interview, x1, y1) ? "interview" : null),
        to: to?.mark ?? (within(interview, x2, y2) ? "interview" : null),
      };
    });
  });
  expect(ends).toEqual([
    ...WAYS_IN.map((mark) => ({ from: mark, to: "interview" })),
    { from: "interview", to: "slack" },
  ]);
});

test("from laptops up, each card's icon tile spans the card's full height", async ({ page }) => {
  test.setTimeout(120_000);
  await page.setViewportSize({ width: 1280, height: 800 });
  const section = await openPicture(page);
  const cards = section.getByTestId("invite-card");
  await expect(cards).toHaveCount(WAYS_IN.length + 1);

  // The tile is the card's first part. Its laid-out box against the card's inside (within its
  // border; the card is its offset parent), so the border and sub-pixel scaling don't count.
  const gaps = await cards.evaluateAll((all) =>
    all.map((card) => {
      const tile = card.firstElementChild as HTMLElement;

      return {
        top: tile.offsetTop,
        bottom: card.clientHeight - (tile.offsetTop + tile.offsetHeight),
      };
    }),
  );
  expect(gaps).toHaveLength(WAYS_IN.length + 1);

  for (const gap of gaps) {
    expect(Math.abs(gap.top)).toBeLessThanOrEqual(1);
    expect(Math.abs(gap.bottom)).toBeLessThanOrEqual(1);
  }
});

test("the developer tools button opens the developer docs", async ({ page }) => {
  test.setTimeout(120_000);
  const section = await openPicture(page);
  // The section's only link.
  await section.getByRole("link").click();
  // The local dev server compiles the docs on first open.
  await expect(page).toHaveURL(/\/api-docs$/, { timeout: 30_000 });
});
