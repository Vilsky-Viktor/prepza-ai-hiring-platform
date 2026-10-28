import { Dotted } from "@/components/dot"
import { DOT_CLASS } from "@/constants/dot"

/** Short facts under a section's picture: from tablets up, one centered line split by the logo's
 * blue dots, a fact staying whole and lines breaking between facts; on phones, one fact a row,
 * each starting with the blue dot, the list centered under the picture. */
export function NotesLine({ notes }: { notes: string[] }) {
  return (
    <div
      data-testid="notes"
      className="text-center text-sm text-balance text-muted-foreground"
    >
      <ul className="mx-auto w-fit space-y-1 text-start sm:hidden">
        {notes.map((note) => (
          <li key={note} className="flex items-center">
            <span aria-hidden className={`${DOT_CLASS} ms-0`} />
            {note}
          </li>
        ))}
      </ul>
      <p className="max-sm:hidden">
        <Dotted
          items={notes.map((note) => (
            <span key={note} className="whitespace-nowrap">
              {note}
            </span>
          ))}
        />
      </p>
    </div>
  )
}
