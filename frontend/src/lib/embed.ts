import { EMBED_LOOKUP_TIMEOUT_MS, EMBED_SOURCE_PATTERN } from "@/config/embed"

/** The sources that may frame an invite's embedded interview, as the companies service decides
 * them: the company's allowed domains (a guest invite's only), none when the page embedding it
 * (`origin`, which the script passes, or the `referrer` the browser sent) is elsewhere. Each
 * source is checked to be one before it goes into the policy. "'none'" for anything else. */
export async function embedAncestors(
  token: string,
  origin?: string | null,
  referrer?: string | null
): Promise<string> {
  const query = new URLSearchParams()

  if (origin) {
    query.set("embed_origin", origin)
  }

  if (referrer) {
    query.set("embed_referrer", referrer)
  }

  try {
    const response = await fetch(
      `${process.env.API_URL}/api/companies/invites/${encodeURIComponent(token)}?${query}`,
      {
        cache: "no-store",
        signal: AbortSignal.timeout(EMBED_LOOKUP_TIMEOUT_MS),
      }
    )
    const found = response.ok
      ? ((await response.json()).embed_ancestors as unknown)
      : null
    const sources = Array.isArray(found)
      ? found.filter(
          (source): source is string =>
            typeof source === "string" && EMBED_SOURCE_PATTERN.test(source)
        )
      : []

    return sources.length ? sources.join(" ") : "'none'"
  } catch {
    return "'none'"
  }
}

/** Where `origin` is a page's own origin ("https://jobs.acme.com"), so messages can go to it. */
export function originOf(value: string | string[] | undefined) {
  try {
    const url = new URL(typeof value === "string" ? value : "")

    return url.origin === value ? value : null
  } catch {
    return null
  }
}
