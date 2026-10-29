"use client"

import { cn } from "cn"
import Link from "next/link"
import { Fragment, type ReactNode } from "react"

import { MenuCount } from "@/components/common/menu-count"
import { PhoneTabs } from "@/components/common/phone-tabs"
import type { MenuIcon, TabItem } from "@/components/common/tab-nav"

/** A page of a page menu; `sub` are its own pages, shown under it while it's open (`keepCase`
 * keeps a name's capitals, as a page's own). */
export type SideMenuItem = TabItem & {
  sub?: readonly {
    id: string
    href: string
    label: string
    keepCase?: boolean
  }[]
}

/** A page with a menu of its pages: on wide screens a list of its pages, each with its icon, at
 * the content's start side, that stays in view while the content scrolls and scrolls itself when
 * taller than the screen (its scrollbar shown on hover); on phones and narrow screens the site's
 * tabs above the content. The open page is on a grey row, with its icon in the page's colour
 * as the only accent. */
export function SideMenuLayout({
  items,
  current,
  currentSub,
  className,
  children,
}: {
  items: readonly SideMenuItem[]
  current: string
  currentSub?: string
  // The content's spacing, as the page's.
  className?: string
  children: ReactNode
}) {
  return (
    <div className="space-y-8 lg:grid lg:grid-cols-[14rem_minmax(0,1fr)] lg:items-start lg:space-y-0 lg:gap-x-10 lg:pt-4">
      <div className="lg:hidden">
        <PhoneTabs items={items} current={current} currentSub={currentSub} />
      </div>
      {/* The padding keeps the rows' focus rings inside the scrolling box. Links straight in the
          nav, as the tabs have them, so the page's own lists stay the only lists in it. */}
      <nav className="sticky top-6 -m-1 flex max-h-[calc(100dvh-3rem)] [scrollbar-color:transparent_transparent] flex-col gap-1.5 overflow-y-auto overscroll-contain p-1 focus-within:[scrollbar-color:var(--border)_transparent] hover:[scrollbar-color:var(--border)_transparent] max-lg:hidden">
        {items.map((item) => (
          <Fragment key={item.id}>
            <MenuLink
              href={item.href ?? ""}
              label={item.label}
              icon={item.icon}
              keepCase={item.keepCase}
              count={item.count}
              open={item.id === current}
              // A page with pages of its own: the row of the open one under it is marked.
              marked={item.id === current && !item.sub}
            />
            {item.id === current &&
              item.sub?.map((sub) => (
                <MenuLink
                  key={sub.id}
                  href={sub.href}
                  label={sub.label}
                  keepCase={sub.keepCase}
                  open={sub.id === currentSub}
                  marked={sub.id === currentSub}
                  nested
                />
              ))}
          </Fragment>
        ))}
      </nav>
      <div className={cn("min-w-0 space-y-8", className)}>{children}</div>
    </div>
  )
}

/** One page in the side menu: the open one in the text's colour with its icon in the page's,
 * the page itself on a grey row; a page under another lines up with the labels. */
function MenuLink({
  href,
  label,
  icon: Icon,
  keepCase,
  count,
  open,
  marked,
  nested,
}: {
  href: string
  label: string
  icon?: MenuIcon
  keepCase?: boolean
  count?: number
  open: boolean
  marked: boolean
  nested?: boolean
}) {
  return (
    <Link
      href={href}
      aria-current={marked ? "page" : undefined}
      className={cn(
        "flex items-center gap-3 rounded-xl px-3 text-base transition-colors outline-none focus-visible:ring-3 focus-visible:ring-ring/50",
        nested ? "py-2 ps-11" : "py-2.5",
        keepCase ? "normal-case" : "lowercase",
        marked
          ? "bg-surface text-foreground"
          : open
            ? "text-foreground hover:bg-surface"
            : "text-muted-foreground hover:bg-surface hover:text-foreground"
      )}
    >
      {Icon && (
        <Icon
          aria-hidden
          className={cn("size-5 shrink-0", open && "text-primary")}
        />
      )}
      {/* Ending with the logo's blue dot, as the site's titles do. */}
      <span className="min-w-0 flex-1">
        {label}
        <span className="blue-dot">.</span>
      </span>
      <MenuCount count={count} />
    </Link>
  )
}
