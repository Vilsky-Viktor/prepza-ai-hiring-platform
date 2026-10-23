import type { ReactNode } from "react"

/** One group of a brand page's settings, a row of its card: its name, what it covers, then its
 * fields side by side. */
export function BrandGroup({
  id,
  name,
  text,
  children,
}: {
  id: string
  name: string
  text: string
  children: ReactNode
}) {
  return (
    <li className="space-y-4 p-6" data-testid={`brand-${id}`}>
      <div className="space-y-1">
        <span className="block text-xl font-medium">{name}</span>
        <p className="text-sm text-muted-foreground">{text}</p>
      </div>
      <div className="flex flex-wrap gap-4">{children}</div>
    </li>
  )
}
