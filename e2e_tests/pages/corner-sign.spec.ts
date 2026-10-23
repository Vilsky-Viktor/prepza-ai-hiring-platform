import { expect, test } from "@playwright/test";

// A card's sign (CornerSign) runs under the card's start edge, which clips it: in a left-to-right
// page it starts before the card's left edge, in a right-to-left one it ends after its right
// edge, and it never crosses the end edge. The guides' start card is checked.

for (const [path, direction] of [
  ["/guides/hiring-engineers", "ltr"],
  ["/he/guides/hiring-engineers", "rtl"],
] as const) {
  test(`the start card's sign is clipped at its start edge (${direction})`, async ({ page }) => {
    await page.goto(path);

    const card = page.getByTestId("start-card");
    const sign = card.getByTestId("corner-sign");
    await expect(sign).toBeAttached();
    const cardBox = (await card.boundingBox())!;
    const signBox = (await sign.boundingBox())!;
    const cardEnd = cardBox.x + cardBox.width;
    const signEnd = signBox.x + signBox.width;

    if (direction === "ltr") {
      expect(signBox.x).toBeLessThan(cardBox.x);
      expect(signEnd).toBeGreaterThan(cardBox.x);
      expect(signEnd).toBeLessThan(cardEnd);
    } else {
      expect(signEnd).toBeGreaterThan(cardEnd);
      expect(signBox.x).toBeLessThan(cardEnd);
      expect(signBox.x).toBeGreaterThan(cardBox.x);
    }

    // Centred on the card's height, whatever that is.
    const middle = (box: { y: number; height: number }) => box.y + box.height / 2;
    expect(Math.abs(middle(signBox) - middle(cardBox))).toBeLessThan(1);
  });
}
