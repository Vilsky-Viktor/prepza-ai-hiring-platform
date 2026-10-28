// Schemes that run or read something in the browser instead of opening a page or an app: an
// address from an answer is never followed to one (React guards links' href; this guards
// window.location).
const SCRIPT_SCHEMES = new Set([
  "javascript:",
  "data:",
  "vbscript:",
  "blob:",
  "file:",
])

/** Whether the browser may go to `url`, an absolute address an answer gave (a page, or a
 * desktop app's own scheme such as cursor://): never one that runs in the page. */
export function safeToOpen(url: unknown): url is string {
  if (typeof url !== "string") {
    return false
  }

  try {
    return !SCRIPT_SCHEMES.has(new URL(url).protocol)
  } catch {
    return false
  }
}

/** Goes to `url` when it's safe to open; otherwise throws, which callers show as a failure. */
export function openAddress(url: unknown) {
  if (!safeToOpen(url)) {
    throw new Error("Refused to open an address that runs in the page")
  }

  window.location.assign(url)
}
