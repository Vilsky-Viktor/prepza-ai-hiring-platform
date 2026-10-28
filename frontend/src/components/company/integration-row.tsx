import Link from "next/link"
import type { ReactNode } from "react"

import {
  INTEGRATION_LINK,
  INTEGRATION_LOGO,
  INTEGRATION_ROW,
} from "@/constants/lists"

/** One row of the integrations tab, laid out like the companies list: the logo tile the row's
 * full height, the name with its status tag, a line of text; the row opens `href`, the buttons
 * (`actions`, a group of INTEGRATION_ACTIONS) sit on top. On phones the logo is a small tile
 * beside the name, and the buttons share the line under it equally, each on its own line where
 * they don't fit and a third always on its own (Reconnect). */
export function IntegrationRow({
  href,
  logo,
  logoClassName = "",
  name,
  status,
  text,
  actions,
}: {
  href: string
  logo: ReactNode
  logoClassName?: string
  name: ReactNode
  status?: ReactNode
  text?: ReactNode
  actions: ReactNode
}) {
  return (
    <li className={INTEGRATION_ROW}>
      <Link href={href} className={INTEGRATION_LINK}>
        <span className={`${INTEGRATION_LOGO} ${logoClassName}`}>{logo}</span>
        <span className="min-w-0 space-y-1">
          <span className="flex items-center gap-3 text-lg font-medium">
            {name}
            {status}
          </span>
          {text && (
            <span className="block text-base text-muted-foreground">
              {text}
            </span>
          )}
        </span>
      </Link>
      <span className="relative z-10 max-sm:col-span-2 max-sm:*:flex max-sm:*:w-full max-sm:*:flex-wrap max-sm:[&>*>*]:flex-1 max-sm:[&>*>*]:px-3 max-sm:[&>*>*:nth-child(3)]:basis-full">
        {actions}
      </span>
    </li>
  )
}
