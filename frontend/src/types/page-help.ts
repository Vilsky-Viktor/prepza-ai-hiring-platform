import type { PAGE_HELP_KEYS } from "@/constants/page-help"

// A page with a guide: every page where the assistant's panel opens.
export type PageHelpKey = (typeof PAGE_HELP_KEYS)[number]

// A page's guide, as rounds serves it.
export type PageGuide = {
  key: PageHelpKey
  title: string
  text: string
  actions: string[]
  tips: string[]
  // The guide article to read more in, in the page's language where translated.
  article: { title: string; path: string } | null
}
