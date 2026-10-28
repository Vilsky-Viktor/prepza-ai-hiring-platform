import path from "node:path"

// The English content pages, as Markdown with frontmatter: the category pages (pages/), the
// comparisons (compare/) and the guides (guides/). Each folder is served under its address.
export const CONTENT_ROOT = path.join(process.cwd(), "content")

export type ContentFolder = "pages" | "compare" | "guides"

// The category pages, each at its own top-level address (/pre-employment-testing).
export const CATEGORY_PAGES = ["pre-employment-testing", "ai-interviews"]
