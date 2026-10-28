import type { ReactNode } from "react"

import { LIST_BOX } from "@/config/lists"

/** What a support page knows about something, one fact a row: its name, then its value. A fact
 * with nothing to say (no value) is left out. */
export function SupportFacts({
  facts,
}: {
  facts: [label: string, value: ReactNode][]
}) {
  return (
    <dl className={LIST_BOX}>
      {facts
        .filter(
          ([, value]) => value !== null && value !== undefined && value !== ""
        )
        .map(([label, value]) => (
          // On phones the value goes under its name.
          <div
            key={label}
            className="flex items-baseline justify-between gap-4 p-6 max-sm:flex-col max-sm:gap-1"
          >
            <dt className="text-muted-foreground">{label}</dt>
            <dd className="text-end break-words max-sm:text-start">{value}</dd>
          </div>
        ))}
    </dl>
  )
}
