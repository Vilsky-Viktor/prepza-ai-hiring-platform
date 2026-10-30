"use client"

import {
  CompassIcon,
  ListChecksIcon,
  NotebookPenIcon,
  SettingsIcon,
  UsersIcon,
} from "lucide-react"
import { useTranslations } from "next-intl"

import type { ReactNode } from "react"

import { SideMenuLayout } from "@/components/common/side-menu"
import type { InterviewTab } from "@/lib/interview-page"

/** The interview's page menu beside its tab's content (`children`): its topics, candidates and
 * notes, each with how many there are; Discover when the API says the company may use it (it has
 * topped up); settings only for those who can change them (owners and admins). */
export function InterviewNav({
  href,
  current,
  canEdit,
  discover,
  counts,
  children,
}: {
  href: string
  current: InterviewTab
  canEdit: boolean
  discover: boolean
  // As the API gives them; none shows at 0.
  counts: { topics: number; candidates: number; notes: number }
  children: ReactNode
}) {
  const t = useTranslations("interviews")
  const items = [
    {
      id: "topics",
      href,
      label: t("topicsTab"),
      icon: ListChecksIcon,
      count: counts.topics,
    },
    {
      id: "candidates",
      href: `${href}?tab=candidates`,
      label: t("candidates"),
      icon: UsersIcon,
      count: counts.candidates,
    },
    {
      id: "notes",
      href: `${href}?tab=notes`,
      label: t("notes"),
      icon: NotebookPenIcon,
      count: counts.notes,
    },
    ...(discover
      ? [
          {
            id: "discover",
            href: `${href}?tab=discover`,
            label: t("discover"),
            icon: CompassIcon,
          } as const,
        ]
      : []),
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
