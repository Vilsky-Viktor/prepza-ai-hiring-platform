import { headers } from "next/headers"
import { getLocale } from "next-intl/server"

import { COUNTRY_HEADER } from "@/config/billing"
import { candidatePriceRange } from "@/lib/format"
import { publicFetch, serverFetch, signedIn } from "@/lib/server-api"
import type { Catalog } from "@/types/billing"

/** A billing path with the visitor's country, which billing goes by for someone signed out, or
 * signed in with no currency saved yet. Passed on by the page: its own calls to the API come from
 * the server, not the visitor. */
async function withCountry(path: string) {
  const country = (await headers()).get(COUNTRY_HEADER)

  return country ? `${path}?country=${encodeURIComponent(country)}` : path
}

/** The FAQ, its prices in the visitor's country's currency. */
export function faqPath() {
  return withCountry("/site/help/faq")
}

/** The signed-in person's currency, and the ones they can choose. */
export function currencyPath() {
  return withCountry("/billing/me/currency")
}

/** The currency a company pays in, and the ones it can choose: for a company with none saved
 * yet, its visitor's country's. */
export function companyCurrencyPath(companyId: string) {
  return withCountry(`/companies/companies/${companyId}/billing/currency`)
}

/** Every price in the visitor's country's currency, the same for every visitor from there: for
 * what search engines read (page descriptions), not a signed-in person's own. */
export async function countryCatalog() {
  return publicFetch<Catalog>(await withCountry("/billing/catalog")).catch(
    () => null
  )
}

/** Every price, in the currency billing decides for the visitor: their own when signed in, else
 * their country's; null when billing is slow or down, so the page shows without prices. */
export async function visitorCatalog() {
  const path = await withCountry("/billing/catalog")

  // Signed in with a sign-in that has expired meanwhile: as signed out.
  const own = (await signedIn())
    ? await serverFetch<Catalog>(path).catch(() => null)
    : null

  return own ?? countryCatalog()
}

/** What a message that may name the price per candidate takes: the range ("$2–5") and whether
 * there is one (`priced`, "yes" or "no"), which its select leaves the sentence out without. */
export async function priceValues(catalog: Catalog | null) {
  const price = candidatePriceRange(catalog, await getLocale())

  return { price, priced: price ? "yes" : "no" }
}
