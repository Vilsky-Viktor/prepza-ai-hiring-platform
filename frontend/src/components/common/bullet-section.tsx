import type { ReactNode } from "react"

/** A statement page's section in the running-text column: its title and a bulleted list (the
 * accessibility statement, the trust page). */
export function BulletSection({
  title,
  items,
}: {
  title: string
  items: ReactNode[]
}) {
  return (
    <section className="mx-auto max-w-5xl space-y-4">
      <h2 className="font-heading text-2xl font-medium tracking-tight">
        {title}
      </h2>
      <ul className="list-disc space-y-2 ps-6 text-base leading-relaxed text-muted-foreground">
        {/* Index keys: the items are fixed lists in a fixed order. */}
        {items.map((item, index) => (
          <li key={index}>{item}</li>
        ))}
      </ul>
    </section>
  )
}
