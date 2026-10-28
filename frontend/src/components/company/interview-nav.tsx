"use client"

import { ListChecksIcon, SettingsIcon, UsersIcon } from "lucide-react"
import { useTranslations } from "next-intl"

import type { ReactNode } from "react"

import { SideMenuLayout } from "@/components/side-menu"

/** The interview's page menu beside its tab's content (`children`); settings only for those who can change them (owners and admins). */
export function InterviewNav({
  href,
  current,
  canEdit,
  children,
}: {
  href: string
  current: "topics" | "candidates" | "settings"
  canEdit: boolean
  children: ReactNode
}) {
  const t = useTranslations("interviews")
  const items = [
    { id: "topics", href, label: t("topicsTab"), icon: ListChecksIcon },
    {
      id: "candidates",
      href: `${href}?tab=candidates`,
      label: t("candidates"),
      icon: UsersIcon,
    },
    ...(canEdit
      ? [
          {
            id: "settings",
            href: `${href}?tab=settings`,
            label: t("settings"),
            icon: SettingsIcon,
          } as const,
        ]
      : []),
  ]

  return (
    <SideMenuLayout items={items} current={current}>
      {children}
    </SideMenuLayout>
  )
}
