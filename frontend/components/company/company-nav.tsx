"use client"

import {
  BlocksIcon,
  BriefcaseBusinessIcon,
  CreditCardIcon,
  GiftIcon,
  HistoryIcon,
  LayoutTemplateIcon,
  PaletteIcon,
  UsersIcon,
} from "lucide-react"
import { useTranslations } from "next-intl"
import type { ReactNode } from "react"

import { SideMenuLayout } from "@/components/side-menu"

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
 * owner (`canSeeActions`). */
export function CompanyNav({
  companyId,
  current,
  canEdit,
  canSeeActions,
  className,
  children,
}: {
  companyId: string
  current: CompanyTab
  canEdit: boolean
  canSeeActions: boolean
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
      icon: LayoutTemplateIcon,
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
            icon: CreditCardIcon,
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
      icon: GiftIcon,
    },
  ]

  return (
    <SideMenuLayout items={items} current={current} className={className}>
      {children}
    </SideMenuLayout>
  )
}
