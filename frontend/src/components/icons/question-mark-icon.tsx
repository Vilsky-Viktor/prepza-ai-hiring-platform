import type { ComponentProps } from "react"

/** A question mark without lucide's circle, drawn in lucide's stroke style. */
export function QuestionMarkIcon(props: ComponentProps<"svg">) {
  return (
    <svg
      viewBox="8 4 8 16"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      {...props}
    >
      <path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3" />
      <path d="M12 17h.01" />
    </svg>
  )
}
