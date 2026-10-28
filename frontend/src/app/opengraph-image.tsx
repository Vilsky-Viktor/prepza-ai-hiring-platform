import { PREVIEW_SIZE } from "@/config/preview-image"
import english from "../../messages/en.json"
import { drawPreview } from "@/lib/preview-image"

// The site's link preview (LinkedIn, Slack, X): the logo over the home page's promise, for the
// home page and for pages a title can't be drawn for (app/preview/route.tsx draws the others).
export const alt = english.site.homeTitle
export const size = PREVIEW_SIZE
export const contentType = "image/png"

export default function OpenGraphImage() {
  return drawPreview(english.home.title.toLowerCase().split("\n"))
}
