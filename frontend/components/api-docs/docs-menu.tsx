"use client"

import {
  BracesIcon,
  CodeXmlIcon,
  PanelsTopLeftIcon,
  PlugZapIcon,
  WebhookIcon,
} from "lucide-react"
import type { ReactNode } from "react"

import { SideMenuLayout } from "@/components/side-menu"
import type { TabItem } from "@/components/tab-nav"
import type { DocTab } from "@/constants/api-docs"

// Each tab's icon in the menu.
const ICONS = {
  api: CodeXmlIcon,
  webhooks: WebhookIcon,
  sdk: PanelsTopLeftIcon,
  mcp: PlugZapIcon,
  objects: BracesIcon,
} as const

/** The developer docs' menu beside the open tab (`children`), each tab with its icon: the page
 * is a server one, and icons can't be passed to the browser. */
export function DocsMenu({
  tabs,
  current,
  children,
}: {
  tabs: readonly (TabItem & { id: DocTab })[]
  current: DocTab
  children: ReactNode
}) {
  return (
    <SideMenuLayout
      items={tabs.map((tab) => ({ ...tab, icon: ICONS[tab.id] }))}
      current={current}
    >
      {children}
    </SideMenuLayout>
  )
}
