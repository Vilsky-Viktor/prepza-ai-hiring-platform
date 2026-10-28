import { LOCALES, type Locale } from "@/config/i18n"
import { PREVIEW_TITLE_MAX } from "@/config/preview-image"
import { sliceGraphemes } from "@/lib/graphemes"
import { drawPreview } from "@/lib/preview-image"
import { validPreviewSignature } from "@/lib/preview-signature"

/** A page's link preview picture: the logo over the page's title (lib/site.ts previewImage
 * names and signs it for each page; any other title is refused, so nobody can put their own
 * text under the logo). A title's picture never changes, so it's cached for good. It's kept
 * out of image search by its header, not robots.txt: link preview bots such as X's and
 * LinkedIn's follow robots.txt and would show no picture. */
export async function GET(request: Request) {
  const query = new URL(request.url).searchParams
  const title = sliceGraphemes(query.get("title") ?? "", PREVIEW_TITLE_MAX)
  const lang = query.get("lang") ?? ""
  const locale = LOCALES.includes(lang as Locale) ? (lang as Locale) : "en"

  if (!validPreviewSignature(title, lang, query.get("sig") ?? "")) {
    return new Response(null, { status: 404 })
  }

  const image = await drawPreview([title], locale)

  image.headers.set("Cache-Control", "public, max-age=31536000, immutable")
  image.headers.set("X-Robots-Tag", "noindex")

  return image
}
