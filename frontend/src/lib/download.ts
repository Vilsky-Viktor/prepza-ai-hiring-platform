import { authHeaders, checkedResponse } from "@/lib/api"

// The file's name in a Content-Disposition header.
const FILE_NAME = /filename="([^"]+)"/

/** Saves the file the API answers `path` with, under the name the API gives it. */
export async function downloadFile(path: string) {
  const response = await checkedResponse(
    await fetch(`/api${path}`, { headers: await authHeaders() })
  )
  const name =
    FILE_NAME.exec(response.headers.get("Content-Disposition") ?? "")?.[1] ??
    "download"
  const url = URL.createObjectURL(await response.blob())
  const link = document.createElement("a")
  link.href = url
  link.download = name
  link.click()
  URL.revokeObjectURL(url)
}
