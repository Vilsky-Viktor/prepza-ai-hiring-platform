"use client"

import {
  BracesIcon,
  CodeXmlIcon,
  PanelsTopLeftIcon,
  WebhookIcon,
} from "lucide-react"
import type { ReactNode } from "react"

import { McpIcon } from "@/components/mcp-icon"
import { type SideMenuItem, SideMenuLayout } from "@/components/side-menu"
import type { DocTab } from "@/config/api-docs"

// Each tab's icon in the menu.
const ICONS = {
  api: CodeXmlIcon,
  webhooks: WebhookIcon,
  sdk: PanelsTopLeftIcon,
  mcp: McpIcon,
  objects: BracesIcon,
} as const

/** The developer docs' menu beside the open tab (`children`), each tab with its icon: the page
 * is a server one, and icons can't be passed to the browser. The open tab's own pages (`sub`,
 * `currentSub` the open one) are listed under it. */
export function DocsMenu({
  tabs,
  current,
  currentSub,
  children,
}: {
  tabs: readonly (SideMenuItem & { id: DocTab })[]
  current: DocTab
  currentSub?: string
  children: ReactNode
}) {
  return (
    <SideMenuLayout
      items={tabs.map((tab) => ({ ...tab, icon: ICONS[tab.id] }))}
      current={current}
      currentSub={currentSub}
    >
      {children}
    </SideMenuLayout>
  )
}
