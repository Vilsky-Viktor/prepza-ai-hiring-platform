import { Dotted } from "@/components/dot"

/** A centered line of short facts under a section's picture, split by the logo's blue dots; a
 * fact stays whole on one line, and lines break between facts. */
export function NotesLine({ notes }: { notes: string[] }) {
  return (
    <p className="text-center text-sm text-balance text-muted-foreground">
      <Dotted
        items={notes.map((note) => (
          <span key={note} className="whitespace-nowrap">
            {note}
          </span>
        ))}
      />
    </p>
  )
}
