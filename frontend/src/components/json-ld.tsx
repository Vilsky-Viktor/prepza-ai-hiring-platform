/** Structured data for search engines (schema.org), as a JSON-LD script; `<` is escaped so the
 * data can't close the script. */
export function JsonLd({ data }: { data: object }) {
  return (
    <script
      type="application/ld+json"
      dangerouslySetInnerHTML={{
        __html: JSON.stringify(data).replace(/</g, "\\u003c"),
      }}
    />
  )
}
