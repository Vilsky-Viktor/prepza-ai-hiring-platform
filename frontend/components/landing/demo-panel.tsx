// A group of panels, laid out in a column.
export const DEMO_GROUP = "flex flex-col gap-3"

// "create an interview"'s groups: a soft band behind the panels, spanning the screen on phones.
export const DEMO_BAND =
  "-mx-6 flex flex-col gap-3 bg-muted/60 px-6 py-5 sm:mx-0 sm:rounded-[2rem] sm:px-4 dark:bg-muted/30"

// A small grey card on a wired stage (sections 2 and 5): an icon and a short label, stacked in a
// grid cell on phones and tablets, side by side from laptops up.
export const SOURCE_CARD =
  "relative z-10 flex min-w-0 flex-col items-center justify-center gap-1.5 rounded-xl bg-muted px-1.5 py-4 text-center text-sm leading-tight font-medium break-words lowercase lg:flex-row lg:gap-2.5 lg:rounded-2xl lg:px-5 lg:py-3.5 lg:text-base lg:whitespace-nowrap dark:bg-card"

/** A small landing picture with its short label above, if any: a plain card that fills its
 * grid cell, so panels side by side are the same height. Screen readers read the label, not the
 * picture. */
export function DemoPanel({
  ref,
  label,
  children,
}: {
  ref?: React.Ref<HTMLDivElement>
  label?: string
  children: React.ReactNode
}) {
  return (
    <div
      ref={ref}
      data-testid="demo-panel"
      className="flex min-w-0 flex-col gap-3"
    >
      {label && <DemoLabel>{label}</DemoLabel>}
      {/* A picture: hidden from screen readers and out of the keyboard's way (its code box would
          otherwise take focus). */}
      <div
        aria-hidden
        inert
        className="relative flex flex-1 flex-col rounded-3xl border bg-background p-3 text-start text-sm"
      >
        {children}
      </div>
    </div>
  )
}

/** A landing picture's or group's short label, centred. */
export function DemoLabel({ children }: { children: React.ReactNode }) {
  return (
    <p className="text-center font-heading text-lg font-medium lowercase">
      {children}
    </p>
  )
}
