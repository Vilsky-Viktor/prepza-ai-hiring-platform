import type { Page } from "@playwright/test"

/** How many questions count as answered in the session's header ("3 / 10" beside the clock, its
 * `count`). */
export async function answered(page: Page): Promise<string> {
  const count = page.locator("p", { has: page.getByRole("timer") }).getByTestId("count")

  return ((await count.textContent()) ?? "").split("/")[0].trim()
}
