import { readFile } from "node:fs/promises"

import { expect, test } from "@playwright/test"

import { zipEntries } from "./helpers/zip"

// The landing's report samples, beside "create an interview" under the reports: a ZIP of the
// two PDF reports, the candidates' and one candidate's, saved when clicked.
test("the report samples download a ZIP of the two PDF reports", async ({ page }) => {
  // The local dev server compiles the home page on first open.
  test.setTimeout(120_000)
  await page.goto("/")
  const link = page.locator("#reports").getByTestId("report-samples")
  await expect(link).toHaveCount(1)
  await expect(link).toHaveAttribute("download", "")
  await link.scrollIntoViewIfNeeded()

  const downloaded = page.waitForEvent("download")
  await link.click()
  const file = await downloaded
  expect(file.suggestedFilename()).toBe("prepza-report-samples.zip")
  const path = test.info().outputPath(file.suggestedFilename())
  await file.saveAs(path)

  const entries = zipEntries(await readFile(path))
  expect([...entries.keys()].sort()).toEqual([
    "prepza-sample-candidate-report.pdf",
    "prepza-sample-candidates.pdf",
  ])

  for (const pdf of entries.values()) {
    expect(pdf.subarray(0, 5).toString()).toBe("%PDF-")
  }
})
