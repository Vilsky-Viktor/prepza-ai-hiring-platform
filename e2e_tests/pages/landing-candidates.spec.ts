import { expect, test } from "@playwright/test";

import { loaded } from "./helpers/waits";

// The home page's candidates section plays a question as a candidate sees it. Its counter
// ("3 / 10") keeps its numbers in order on right-to-left pages too, never mirrored to "10 / 3":
// Hebrew writes Western digits and Arabic its own, which bidi orders differently (Persian's
// digits order as Western ones do).

for (const locale of ["he", "ar"]) {
  test(`the demo question's counter reads answered, then total, in ${locale}`, async ({
    page,
  }) => {
    await page.goto(`/${locale}`);
    await loaded(page);
    const count = page.getByRole("main").getByTestId("count").first();
    await count.scrollIntoViewIfNeeded();
    await expect(count).toBeVisible();

    // Where each number starts on screen: the answered one sits to the left of the total.
    const [answered, total] = await count.evaluate((element) => {
      const numbers = [...element.childNodes].filter((node) => node.textContent?.trim());
      const left = (node: Node) => {
        const range = document.createRange();
        range.selectNodeContents(node);

        return range.getBoundingClientRect().left;
      };

      return [left(numbers[0]), left(numbers[numbers.length - 1])];
    });
    expect(answered).toBeLessThan(total);
  });
}

// The switch above the picture jumps the demo to the mode a visitor picks, back and forth, and
// shows which is on; the frame keeps its size and place as the screens change.
test("the mode switch jumps the demo to either mode, and the frame never moves", async ({
  page,
}) => {
  test.setTimeout(120_000);
  await page.goto("/");
  await loaded(page);
  const section = page.locator("#candidates");
  await section.scrollIntoViewIfNeeded();
  const demo = section.getByTestId("candidates-demo");
  const frame = demo.getByTestId("demo-panel");
  const box = () =>
    frame.evaluate((element) => {
      const rect = element.getBoundingClientRect();

      return [rect.width, rect.height, rect.left, rect.top + window.scrollY].map(Math.round).join();
    });
  const [click, voice] = [demo.getByRole("button").nth(0), demo.getByRole("button").nth(1)];
  // Playing once in view: its steps move on.
  const first = await demo.getAttribute("data-step");
  await expect(demo).not.toHaveAttribute("data-step", first!);
  const before = await box();

  await voice.click();
  await expect(voice).toHaveAttribute("aria-pressed", "true");
  await expect(click).toHaveAttribute("aria-pressed", "false");
  // Voice steps are named v…, click ones c… or by their question.
  await expect(demo).toHaveAttribute("data-step", /^v/);
  expect(await box()).toBe(before);

  await click.click();
  await expect(click).toHaveAttribute("aria-pressed", "true");
  await expect(demo).toHaveAttribute("data-step", /^(?!v)/);
  expect(await box()).toBe(before);
});

test("on a phone the modes show as cards in place of the demo", { tag: "@phone-only" }, async ({
  page,
}) => {
  test.setTimeout(120_000);
  await page.goto("/");
  const section = page.locator("#candidates");
  await section.scrollIntoViewIfNeeded();

  await expect(section.getByTestId("candidates-demo")).toBeHidden();
  await expect(section.getByTestId("phone-steps").getByTestId("icon-card")).toHaveCount(2);
  await expect(section.getByTestId("notes")).toBeVisible();
});
