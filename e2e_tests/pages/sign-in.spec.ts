import { expect, test } from "@playwright/test";

// The sign-in card asks a new account about emails; once someone has signed in on this browser,
// it leaves the choices out (an account's are in its settings).
test("the sign-in card asks about emails only on a browser not signed in before", async ({
  page,
}) => {
  test.setTimeout(120_000);
  await page.goto("/companies");
  const offers = page.getByTestId("email-box-promotions");
  await expect(offers).toBeVisible();

  await page.evaluate(() =>
    localStorage.setItem("testee:signed-in-before", "1"),
  );
  await page.reload();
  await expect(page.getByTestId("sign-in-google")).toBeVisible();
  await expect(offers).toBeHidden();
});
