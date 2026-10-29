import { expect, test } from "../fixtures"
import { api, createCompany } from "../helpers/api"
import { settled } from "../helpers/layout"
import { visit } from "../helpers/navigation"
import { shot } from "../helpers/screenshots"
import { ownerEmail } from "../helpers/users"

test("an owner stops AI apps from using the company's data, and allows them again", async ({
  signInAs,
  signInWith,
}) => {
  const email = ownerEmail()
  const owner = await signInAs(email)
  const company = await createCompany(owner)

  await visit(owner, `/companies/${company.id}/integrations/ai`)
  const allow = owner.getByRole("switch")
  await expect(allow).toBeChecked()
  await shot(owner, "allowed")

  await allow.click()
  await expect(allow).not.toBeChecked()
  await expect
    .poll(async () => (await api<{ ai_apps_allowed: boolean }>(owner, "GET", `/companies/companies/${company.id}`)).ai_apps_allowed)
    .toBe(false)
  await shot(owner, "stopped")

  // Kept after a reload.
  await owner.reload()
  await expect(allow).not.toBeChecked()
  await allow.click()
  await expect(allow).toBeChecked()

  // Right to left (Arabic): the knob stays inside its track, on and off.
  // A new sign-in's token carries the account's new language.
  await api(owner, "PUT", "/accounts/me/settings", { language: "ar" })
  const arabic = await signInWith(email, false)
  await visit(arabic, `/companies/${company.id}/integrations/ai`)
  await expect(arabic.locator("html")).toHaveAttribute("dir", "rtl")
  const switchAr = arabic.getByRole("switch")

  for (const checked of [true, false]) {
    await expect(switchAr).toBeChecked({ checked })
    await settled(switchAr)
    const track = (await switchAr.boundingBox())!
    const knob = (await switchAr.locator("[data-slot=switch-thumb]").boundingBox())!
    expect(knob.x).toBeGreaterThanOrEqual(track.x - 1)
    expect(knob.x + knob.width).toBeLessThanOrEqual(track.x + track.width + 1)
    await shot(arabic, checked ? "rtl-on" : "rtl-off")

    if (checked) {
      await switchAr.click()
    }
  }
})
