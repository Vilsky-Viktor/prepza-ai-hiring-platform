"use client"

import { KeyRoundIcon, WebhookIcon } from "lucide-react"
import { useTranslations } from "next-intl"

import type { ReactNode } from "react"

import { SideMenuLayout } from "@/components/side-menu"

/** The API page's menu beside its content (`children`): its keys, and its web hooks. */
export function ApiNav({
  href,
  current,
  children,
}: {
  href: string
  current: "keys" | "webhooks"
  children: ReactNode
}) {
  const t = useTranslations("api")
  const items = [
    {
      id: "keys",
      href,
      label: t("keysTitle"),
      keepCase: true,
      icon: KeyRoundIcon,
    },
    {
      id: "webhooks",
      href: `${href}?tab=webhooks`,
      label: t("webhooksTitle"),
      icon: WebhookIcon,
    },
  ]

  return (
    <SideMenuLayout items={items} current={current}>
      {children}
    </SideMenuLayout>
  )
}
