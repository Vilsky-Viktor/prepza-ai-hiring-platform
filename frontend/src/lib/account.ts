import { apiFetch } from "@/lib/api"

/** Saves everything testee holds about the user as testee-data.json. */
export async function downloadMyData() {
  const data = await apiFetch<unknown>("/accounts/me/export")
  const url = URL.createObjectURL(
    new Blob([JSON.stringify(data, null, 2)], { type: "application/json" })
  )
  const link = document.createElement("a")
  link.href = url
  link.download = "testee-data.json"
  link.click()
  URL.revokeObjectURL(url)
}
