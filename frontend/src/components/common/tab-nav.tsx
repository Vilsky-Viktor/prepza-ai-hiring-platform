"use client"

import { cn } from "cn"
import Link from "next/link"
import { type ComponentType, type ReactNode, useEffect, useRef } from "react"

import { MenuCount } from "@/components/common/menu-count"
import { CURRENT_TAB } from "@/config/tab-nav"

/** A menu item's icon: a lucide icon or another icon sized by its class (McpIcon). */
export type MenuIcon = ComponentType<{
  className?: string
  "aria-hidden"?: boolean | "true" | "false"
}>

/** One tab: a link to `href`, or with `onSelect` a button; `count` shows after its label. */
export type TabItem = {
  id: string
  href?: string
  label: string
  keepCase?: boolean
  icon?: MenuIcon
  count?: number
}

/** A page's slim tabs under its title: the current one over a blue line. Labels are lowercase
 * like the site's other tabs; `keepCase` keeps an abbreviation's capitals (ATS). Tabs wider than
 * the screen scroll in their own row, with the current one brought into view. With `onSelect`
 * they're tabs within a page or a dialog (buttons) rather than links, fitting its width, and
 * control the `TabPanel` whose id is `panel`; an item's `icon` goes before its label, in the
 * label's colour. `more` goes at the row's end (the side menu's "more pages" on phones). */
export function TabNav({
  items,
  current,
  onSelect,
  panel,
  more,
}: {
  items: readonly TabItem[]
  current: string
  onSelect?: (id: string) => void
  // With onSelect: the id of the panel the tabs show (useId in the caller).
  panel?: string
  more?: ReactNode
}) {
  const active = useRef<HTMLAnchorElement & HTMLButtonElement>(null)

  const row = useRef<HTMLDivElement>(null)

  // The current tab brought into view by scrolling the row alone: scrollIntoView would also
  // move where the keyboard's Tab starts, past the skip link and the header.
  useEffect(() => {
    const tab = active.current?.getBoundingClientRect()
    const box = row.current?.getBoundingClientRect()

    if (!tab || !box) {
      return
    }

    const before = tab.left - box.left
    const after = tab.right - box.right
    row.current?.scrollBy({ left: before < 0 ? before : Math.max(after, 0) })
  }, [current])

  // As a tablist: the arrow keys move to the next or previous tab (mirrored right to left),
  // Home and End to the first and last, and the tab it lands on is selected and focused.
  function onKeyDown(event: React.KeyboardEvent<HTMLElement>) {
    const rtl = getComputedStyle(event.currentTarget).direction === "rtl"
    const step = { ArrowRight: rtl ? -1 : 1, ArrowLeft: rtl ? 1 : -1 }[
      event.key
    ]
    const index = items.findIndex((item) => item.id === current)
    const next =
      event.key === "Home"
        ? 0
        : event.key === "End"
          ? items.length - 1
          : step === undefined
            ? null
            : (index + step + items.length) % items.length

    if (next === null || !onSelect) {
      return
    }

    event.preventDefault()
    onSelect(items[next].id)
    const tabs =
      event.currentTarget.querySelectorAll<HTMLElement>('[role="tab"]')
    tabs[next]?.focus()
  }

  return (
    // The row scrolls; the line under the tabs is the inner row's, so the current tab's blue
    // line isn't clipped.
    <div ref={row} className="[scrollbar-width:none] overflow-x-auto">
      <nav
        role={onSelect ? "tablist" : undefined}
        onKeyDown={onSelect ? onKeyDown : undefined}
        // Tabs inside a dialog fit its width: closer together on a phone, a long label wraps.
        className={cn(
          "flex border-b",
          onSelect
            ? "w-full items-end gap-3 sm:gap-5"
            : "w-max min-w-full gap-8"
        )}
      >
        {items.map((item) => {
          const className = cn(
            "-mb-px border-b-2 pb-3 transition-colors",
            // In a dialog on a phone, a step smaller, and a long word breaks.
            onSelect
              ? "text-start text-sm hyphens-auto sm:text-base"
              : "text-base whitespace-nowrap",
            item.keepCase ? "normal-case" : "lowercase",
            item.id === current
              ? CURRENT_TAB
              : "border-transparent text-muted-foreground hover:text-foreground active:border-border active:text-foreground"
          )

          return onSelect ? (
            <button
              key={item.id}
              ref={item.id === current ? active : undefined}
              type="button"
              role="tab"
              id={panel && tabId(panel, item.id)}
              aria-selected={item.id === current}
              aria-controls={panel}
              // Only the current tab is in the Tab order; the arrow keys reach the others.
              tabIndex={item.id === current ? 0 : -1}
              className={className}
              onClick={() => onSelect(item.id)}
            >
              {item.icon ? (
                <span className="flex items-center gap-1.5">
                  <item.icon aria-hidden className="size-4 shrink-0" />
                  <span>{item.label}</span>
                </span>
              ) : (
                item.label
              )}
            </button>
          ) : (
            <Link
              key={item.id}
              ref={item.id === current ? active : undefined}
              href={item.href ?? ""}
              aria-current={item.id === current ? "page" : undefined}
              className={cn(className, "flex items-center gap-2")}
            >
              {item.label}
              <MenuCount count={item.count} />
            </Link>
          )
        })}
        {more}
      </nav>
    </div>
  )
}

/** The id of the tab `id` of the tabs that show `panel`, which names the panel. */
export function tabId(panel: string, id: string) {
  return `${panel}-tab-${id}`
}

/** What the current tab of a TabNav with `onSelect` shows: its panel, named by the tab. */
export function TabPanel({
  id,
  current,
  className,
  children,
}: {
  // The panel's id, as the TabNav's `panel`.
  id: string
  current: string
  className?: string
  children: React.ReactNode
}) {
  return (
    <div
      role="tabpanel"
      id={id}
      aria-labelledby={tabId(id, current)}
      className={className}
    >
      {children}
    </div>
  )
}
