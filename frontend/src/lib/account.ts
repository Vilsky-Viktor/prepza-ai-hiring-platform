import { apiFetch } from "@/lib/api"

/** Saves everything prepza holds about the user as prepza-data.json. */
export async function downloadMyData() {
  const data = await apiFetch<unknown>("/library/me/export")
  const url = URL.createObjectURL(
    new Blob([JSON.stringify(data, null, 2)], { type: "application/json" })
  )
  const link = document.createElement("a")
  link.href = url
  link.download = "prepza-data.json"
  link.click()
  URL.revokeObjectURL(url)
}
