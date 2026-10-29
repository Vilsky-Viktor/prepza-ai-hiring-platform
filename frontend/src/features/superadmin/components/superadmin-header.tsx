"use client"

import { useTranslations } from "next-intl"
import type { ReactNode } from "react"

import {
  SuperadminMenu,
  type SuperadminPage,
} from "@/features/superadmin/components/superadmin-menu"

/** The admin zone's title, with `action` on the right, and its menu beside the page's content
 * (`children`), as a company's pages have them. Questions and stats have pages of their own,
 * listed under them while open: `sub` is the one open. */
export function SuperadminHeader({
  current,
  sub,
  action,
  children,
}: {
  current: SuperadminPage
  sub?: "flagged" | "replaced" | "patterns" | "general" | "ai-costs"
  action?: ReactNode
  children: ReactNode
}) {
  const t = useTranslations("superadmin")

  return (
    <div className="space-y-4">
      {/* On phones the action takes its own line under the title, at full width. */}
      <div className="flex min-h-14 items-center max-sm:flex-wrap">
        <h1 className="min-w-0 flex-1 font-heading text-3xl font-medium tracking-tight max-sm:basis-full">
          {t("zone")}
        </h1>
        {action && (
          <div className="max-sm:my-4 max-sm:basis-full max-sm:*:w-full">
            {action}
          </div>
        )}
      </div>
      <SuperadminMenu current={current} sub={sub}>
        {children}
      </SuperadminMenu>
    </div>
  )
}
