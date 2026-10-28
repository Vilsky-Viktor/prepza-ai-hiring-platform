import type { Page } from "@playwright/test"

// A test that wants a scheme sets the device's setting and also picks it as a visitor would
// (next-themes' saved choice, "theme" in localStorage), so the page shows it however it decides.

/** Shows `page` in `scheme` from now on: the device's setting and the saved choice both, on the
 * page that's open and on every page it loads next. */
export async function setScheme(page: Page, scheme: "light" | "dark") {
  await page.emulateMedia({ colorScheme: scheme })
  // Init scripts run in the order they were added, so the latest call wins.
  await page.addInitScript((theme) => localStorage.setItem("theme", theme), scheme)

  if (!page.url().startsWith("http")) {
    return
  }

  // The open page switches now, keeping its state (an open dialog, a flipped switch): the saved
  // choice, and the class and color scheme next-themes would set on <html>.
  await page.evaluate((theme) => {
    localStorage.setItem("theme", theme)
    document.documentElement.classList.remove("light", "dark")
    document.documentElement.classList.add(theme)
    document.documentElement.style.colorScheme = theme
  }, scheme)
}
