"use client"

import { type ReactNode, useId, useState } from "react"

import { TabNav, TabPanel } from "@/components/common/tab-nav"

/** Sections of a page as tabs (the site's TabNav as buttons), the first open: each panel's
 * content is made by the page, so a server page can pass its own. */
export function TabPanels({
  panels,
}: {
  panels: { id: string; label: string; content: ReactNode }[]
}) {
  const [current, setCurrent] = useState(panels[0]?.id ?? "")
  const panel = useId()

  return (
    <div className="space-y-6">
      <TabNav
        items={panels.map(({ id, label }) => ({ id, label, keepCase: true }))}
        current={current}
        onSelect={setCurrent}
        panel={panel}
      />
      <TabPanel id={panel} current={current}>
        {panels.find((item) => item.id === current)?.content}
      </TabPanel>
    </div>
  )
}
