// Downloads the two sample reports from the development page /report-samples, through its own
// download buttons, into the folder given (scripts/report-samples.sh runs it in Playwright's
// Docker image). Usage: node report-samples.mjs <folder>
import { chromium } from "playwright"

const site = process.env.SITE_URL ?? "http://localhost:8090"
const folder = process.argv[2]
const browser = await chromium.launch({
  args: process.env.HOST_RULES
    ? [`--host-resolver-rules=${process.env.HOST_RULES}`]
    : [],
})

try {
  const page = await browser.newPage({ acceptDownloads: true })
  await page.goto(`${site}/report-samples`, { timeout: 120_000 })
  const buttons = page.getByRole("main").getByRole("button")

  // Each report's download button comes first of its two actions.
  for (const index of [0, 2]) {
    const download = page.waitForEvent("download", { timeout: 60_000 })
    await buttons.nth(index).click()
    const file = await download
    await file.saveAs(`${folder}/${file.suggestedFilename()}`)
    console.log(file.suggestedFilename())
  }
} finally {
  await browser.close()
}
