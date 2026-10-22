// Cache-Control for the files in public/, which Next.js otherwise sends with max-age=0 so every
// view asks again (next.config.ts headers). Hashed build files get a year from Next.js itself.

// Logos and pictures, which keep their content under a name: a day.
export const PICTURE_HEADERS = [
  { key: "Cache-Control", value: "public, max-age=86400" },
]

// Documents and examples, rebuilt in place when they change: an hour, then served while they're
// checked again for a day.
export const DOCUMENT_HEADERS = [
  {
    key: "Cache-Control",
    value: "public, max-age=3600, stale-while-revalidate=86400",
  },
]
