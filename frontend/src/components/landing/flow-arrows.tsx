import { ChevronDownIcon, ChevronRightIcon } from "lucide-react"

// The arrows in the row, and how far apart in time they light up, in seconds.
const ARROWS = [0, 1, 2]
const STEP_SECONDS = 0.25

/** Arrows from one landing panel to the next, in the primary colour, lighting up in turn
 * towards it: across from laptops up, where the panels sit side by side, and down below, where
 * they stack. With reduced motion they stay lit. Decoration only. */
export function FlowArrows() {
  return (
    <div
      aria-hidden
      className="flex items-center justify-center py-3 text-primary lg:px-3 lg:py-0 lg:pt-10"
    >
      <div className="flex flex-col lg:flex-row">
        {ARROWS.map((position) => (
          <span
            key={position}
            style={{ animationDelay: `${position * STEP_SECONDS}s` }}
            className="-my-1.5 animate-[light-up_1.5s_ease-in-out_infinite] motion-reduce:animate-none lg:-mx-1.5 lg:my-0"
          >
            <ChevronDownIcon className="size-6 lg:hidden" />
            <ChevronRightIcon className="hidden size-6 lg:block rtl:-scale-x-100" />
          </span>
        ))}
      </div>
    </div>
  )
}
