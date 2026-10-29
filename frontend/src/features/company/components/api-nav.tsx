"use client"

import { GlobeIcon, KeyRoundIcon, WebhookIcon } from "lucide-react"
import { useTranslations } from "next-intl"

import type { ReactNode } from "react"

import { SideMenuLayout } from "@/components/common/side-menu"

export type ApiTab = "keys" | "webhooks" | "domains"

/** The API page's menu beside its content (`children`): its keys, its web hooks and the SDK's
 * allowed domains. */
export function ApiNav({
  href,
  current,
  children,
}: {
  href: string
  current: ApiTab
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
    {
      id: "domains",
      href: `${href}?tab=domains`,
      label: t("sdkTitle"),
      keepCase: true,
      icon: GlobeIcon,
    },
  ]

  return (
    <SideMenuLayout items={items} current={current}>
      {children}
    </SideMenuLayout>
  )
}
