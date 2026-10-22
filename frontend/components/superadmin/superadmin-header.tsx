"use client"

import {
  BadgeCheckIcon,
  ChartColumnIcon,
  FlagIcon,
  LayoutTemplateIcon,
  LifeBuoyIcon,
  MegaphoneIcon,
  NewspaperIcon,
  PercentIcon,
  SlidersHorizontalIcon,
} from "lucide-react"
import { useTranslations } from "next-intl"
import type { ReactNode } from "react"

import { SideMenuLayout } from "@/components/side-menu"

// The pages with pages of their own: each one's path under its page and its label's message.
const SUBTABS = {
  questions: [
    { id: "flagged", label: "flagged" },
    { id: "replaced", label: "replaced" },
    { id: "patterns", label: "patterns" },
  ],
  stats: [
    { id: "general", label: "statsGeneral" },
    { id: "ai-costs", label: "aiCosts" },
  ],
} as const

/** The admin zone's title, with `action` on the right, and its menu beside the page's content
 * (`children`), as a company's pages have them. Questions and stats have pages of their own,
 * listed under them while open: `sub` is the one open. */
export function SuperadminHeader({
  current,
  sub,
  action,
  children,
}: {
  current:
    | "templates"
    | "questions"
    | "pass-rates"
    | "verification"
    | "support"
    | "stats"
    | "controls"
    | "news"
    | "campaigns"
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
      <SideMenuLayout
        items={[
          {
            id: "templates",
            href: "/superadmin/templates",
            label: t("templates"),
            icon: LayoutTemplateIcon,
          },
          {
            id: "news",
            href: "/superadmin/news",
            label: t("news"),
            icon: NewspaperIcon,
          },
          {
            id: "campaigns",
            href: "/superadmin/campaigns",
            label: t("campaigns"),
            icon: MegaphoneIcon,
          },
          {
            id: "questions",
            href: "/superadmin/questions/flagged",
            label: t("questions"),
            icon: FlagIcon,
            sub: SUBTABS.questions.map(({ id, label }) => ({
              id,
              href: `/superadmin/questions/${id}`,
              label: t(label),
            })),
          },
          {
            id: "pass-rates",
            href: "/superadmin/pass-rates",
            label: t("passRates"),
            icon: PercentIcon,
          },
          {
            id: "verification",
            href: "/superadmin/verification",
            label: t("verification"),
            icon: BadgeCheckIcon,
          },
          {
            id: "support",
            href: "/superadmin/support",
            label: t("support"),
            icon: LifeBuoyIcon,
          },
          {
            id: "stats",
            href: "/superadmin/stats/general",
            label: t("stats"),
            icon: ChartColumnIcon,
            sub: SUBTABS.stats.map(({ id, label }) => ({
              id,
              href: `/superadmin/stats/${id}`,
              label: t(label),
            })),
          },
          {
            id: "controls",
            href: "/superadmin/controls",
            label: t("controls"),
            icon: SlidersHorizontalIcon,
          },
        ]}
        current={current}
        currentSub={sub}
      >
        {children}
      </SideMenuLayout>
    </div>
  )
}
