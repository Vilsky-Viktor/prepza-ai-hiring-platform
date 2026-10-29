"use client"

import {
  ChartColumnIcon,
  FormIcon,
  LifeBuoyIcon,
  MegaphoneIcon,
  MessagesSquareIcon,
  NewspaperIcon,
  PercentIcon,
  ShieldCheckIcon,
  SlidersHorizontalIcon,
} from "lucide-react"
import { useTranslations } from "next-intl"
import type { ReactNode } from "react"

import {
  type SideMenuItem,
  SideMenuLayout,
} from "@/components/common/side-menu"

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

export type SuperadminPage =
  | "templates"
  | "questions"
  | "pass-rates"
  | "verification"
  | "support"
  | "stats"
  | "controls"
  | "news"
  | "campaigns"

/** The admin zone's menu beside a page's content (`children`, spaced by `className`). Questions
 * and stats have pages of their own, listed under them while open; a page can bring its own
 * (`pages`), as a company's support page does its sections. `sub` is the one open. */
export function SuperadminMenu({
  current,
  sub,
  pages,
  className,
  children,
}: {
  current: SuperadminPage
  sub?: string
  pages?: SideMenuItem["sub"]
  className?: string
  children: ReactNode
}) {
  const t = useTranslations("superadmin")
  const items: SideMenuItem[] = [
    {
      id: "templates",
      href: "/superadmin/templates",
      label: t("templates"),
      icon: FormIcon,
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
      icon: MessagesSquareIcon,
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
      icon: ShieldCheckIcon,
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
  ]

  return (
    <SideMenuLayout
      items={items.map((item) =>
        item.id === current && pages ? { ...item, sub: pages } : item
      )}
      current={current}
      currentSub={sub}
      className={className}
    >
      {children}
    </SideMenuLayout>
  )
}
