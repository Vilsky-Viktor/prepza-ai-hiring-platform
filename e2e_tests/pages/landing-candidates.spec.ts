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
