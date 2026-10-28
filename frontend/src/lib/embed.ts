import { EMBED_LOOKUP_TIMEOUT_MS } from "@/config/embed"

/** The sources that may frame an invite's embedded interview: the company's website domain and
 * its subdomains, as the companies service says (a guest invite's only), without a scheme so
 * they match the page's own (https in production). "'none'" for anything else. */
export async function embedAncestors(token: string): Promise<string> {
  try {
    const response = await fetch(
      `${process.env.API_URL}/api/companies/invites/${encodeURIComponent(token)}`,
      {
        cache: "no-store",
        signal: AbortSignal.timeout(EMBED_LOOKUP_TIMEOUT_MS),
      }
    )
    const domain = response.ok
      ? ((await response.json()).embed_domain as string | null)
      : null

    return domain ? `${domain} *.${domain}` : "'none'"
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
