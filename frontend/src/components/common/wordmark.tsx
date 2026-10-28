import { cn } from "cn"

type WordmarkProps = {
  className?: string
  // "p." below the sm breakpoint, so the signed-in header fits a phone.
  shortOnPhones?: boolean
}

export function Wordmark({ className, shortOnPhones = false }: WordmarkProps) {
  return (
    <span
      className={cn("font-heading font-semibold tracking-tight", className)}
    >
      p<span className={cn(shortOnPhones && "hidden sm:inline")}>repza</span>
      <span className="text-primary">.</span>
    </span>
  )
}
