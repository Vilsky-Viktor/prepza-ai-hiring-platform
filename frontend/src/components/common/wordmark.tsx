import { cn } from "cn"

type WordmarkProps = {
  className?: string
  // "t." below the sm breakpoint, so the signed-in header fits a phone.
  shortOnPhones?: boolean
  // "t." alone everywhere, as an avatar's mark.
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
      t
      {!short && (
        <span className={cn(shortOnPhones && "hidden sm:inline")}>estee</span>
      )}
      <span className="blue-dot">.</span>
    </span>
  )
}
