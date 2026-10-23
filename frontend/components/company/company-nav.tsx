"use client"

import {
  BlocksIcon,
  BriefcaseBusinessIcon,
  DollarSignIcon,
  FormIcon,
  HistoryIcon,
  PaletteIcon,
  UsersIcon,
  UsersRoundCollaborationIcon,
} from "lucide-react"
import { useTranslations } from "next-intl"
import type { ReactNode } from "react"

import { type SideMenuItem, SideMenuLayout } from "@/components/side-menu"

export type CompanyTab =
  | "interviews"
  | "templates"
  | "members"
  | "actions"
  | "integrations"
  | "brand"
  | "referrals"
  | "billing"

/** A company's page menu beside its page's content (`children`); brand and billing only for
 * owners and admins (`canEdit`), who set its colors and top up; the action log only for the
 * owner (`canSeeActions`). The open page's own pages (`sub`, `currentSub` the open one) are
 * listed under it. */
export function CompanyNav({
  companyId,
  current,
  canEdit,
  canSeeActions,
  sub,
  currentSub,
  className,
  children,
}: {
  companyId: string
  current: CompanyTab
  canEdit: boolean
  canSeeActions: boolean
  sub?: SideMenuItem["sub"]
  currentSub?: string
  // The content's spacing, as the page's.
  className?: string
  children: ReactNode
}) {
  const t = useTranslations("company")
  const items = [
    {
      id: "interviews",
      href: `/companies/${companyId}/interviews`,
      label: t("interviews"),
      icon: BriefcaseBusinessIcon,
    },
    {
      id: "templates",
      href: `/companies/${companyId}/templates`,
      label: t("templates"),
      icon: FormIcon,
    },
    {
      id: "members",
      href: `/companies/${companyId}/members`,
      label: t("team"),
      icon: UsersIcon,
    },
    {
      id: "integrations",
      href: `/companies/${companyId}/integrations`,
      label: t("integrations"),
      icon: BlocksIcon,
    },
    ...(canEdit
      ? [
          {
            id: "brand",
            href: `/companies/${companyId}/brand`,
            label: t("brand"),
            icon: PaletteIcon,
          },
          {
            id: "billing",
            href: `/companies/${companyId}/billing`,
            label: t("billing"),
            icon: DollarSignIcon,
          },
        ]
      : []),
    ...(canSeeActions
      ? [
          {
            id: "actions",
            href: `/companies/${companyId}/actions`,
            label: t("actions"),
            icon: HistoryIcon,
          },
        ]
      : []),
    {
      id: "referrals",
      href: `/companies/${companyId}/referrals`,
      label: t("referrals"),
      icon: UsersRoundCollaborationIcon,
    },
  ]

  return (
    <SideMenuLayout
      items={items.map((item) =>
        item.id === current ? { ...item, sub } : item
      )}
      current={current}
      currentSub={currentSub}
      className={className}
    >
      {children}
    </SideMenuLayout>
  )
}
