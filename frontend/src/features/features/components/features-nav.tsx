"use client"

import { useEffect, useState } from "react"

import { TabNav } from "@/components/common/tab-nav"
import { STICKY_BAR } from "@/config/landing-backgrounds"

/** The features page's groups as the site's slim tabs, links to each, kept at the top of the
 * window while the page scrolls; the group being read is the current one. */
export function FeaturesNav({
  items,
}: {
  items: { id: string; label: string }[]
}) {
  const [current, setCurrent] = useState(items[0]?.id ?? "")

  // The group crossing a band just above the window's middle is the one being read.
  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        for (const entry of entries) {
          if (entry.isIntersecting) {
            setCurrent(entry.target.id)
          }
        }
      },
      { rootMargin: "-35% 0px -60% 0px" }
    )

    for (const item of items) {
      const section = document.getElementById(item.id)

      if (section) {
        observer.observe(section)
      }
    }

    return () => observer.disconnect()
  }, [items])

  return (
    <div data-sticky-tabs className={`sticky top-0 z-20 pt-3 ${STICKY_BAR}`}>
      <TabNav
        items={items.map((item) => ({ ...item, href: `#${item.id}` }))}
        current={current}
      />
    </div>
  )
}
