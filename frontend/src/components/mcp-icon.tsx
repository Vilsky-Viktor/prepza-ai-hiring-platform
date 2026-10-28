import { cn } from "cn"

import { MCP_MARK } from "@/constants/ai-apps"

/** The MCP mark as an icon: its shape in the current text colour, sized by `className`, so it
 * sits in menus and cards like the other icons (the side menu colours the open page's icon). */
export function McpIcon({
  className,
  "aria-hidden": ariaHidden = true,
}: {
  className?: string
  "aria-hidden"?: boolean | "true" | "false"
}) {
  return (
    <span
      aria-hidden={ariaHidden}
      className={cn("inline-block size-5 shrink-0 bg-current", className)}
      style={{
        mask: `url(${MCP_MARK}) center / contain no-repeat`,
        WebkitMask: `url(${MCP_MARK}) center / contain no-repeat`,
      }}
    />
  )
}
