import { cn } from "cn"

type WordmarkProps = {
  className?: string
  // "p." below the sm breakpoint, so the signed-in header fits a phone.
  shortOnPhones?: boolean
  // "p." alone everywhere, as an avatar's mark.
  short?: boolean
}

export function Wordmark({
  className,
  shortOnPhones = false,
  short = false,
}: WordmarkProps) {
  return (
    <span
      className={cn("font-heading font-semibold tracking-tight", className)}
    >
      p
      {!short && (
        <span className={cn(shortOnPhones && "hidden sm:inline")}>repza</span>
      )}
      <span className="blue-dot">.</span>
    </span>
  )
}
