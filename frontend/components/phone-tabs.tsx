"use client"

import { cn } from "cn"
import { CheckIcon, ChevronDownIcon, MoreHorizontalIcon } from "lucide-react"
import Link from "next/link"
import { useTranslations } from "next-intl"
import { useId } from "react"

import type { SideMenuItem } from "@/components/side-menu"
import { TabNav } from "@/components/tab-nav"
import { Button } from "@/components/ui/button"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { MENU_PILL_CHEVRON_CLASS, MENU_PILL_CLASS } from "@/constants/menu-pill"
import { splitPhoneTabs } from "@/lib/phone-tabs"

/** A page menu on phones and narrow screens: the site's tabs, the first three in the row and
 * the others, in their order, in a menu under a "…" button; an open page from that menu takes
 * the third place. A page with pages of its own (`sub`) names the open one in a bar under the row,
 * which opens the list of them all. */
export function PhoneTabs({
  items,
  current,
  currentSub,
}: {
  items: readonly SideMenuItem[]
  current: string
  currentSub?: string
}) {
  const t = useTranslations("common")
  const { shown, rest } = splitPhoneTabs(items, current)
  const open = items.find((item) => item.id === current)

  return (
    <div>
      <TabNav
        items={shown}
        current={current}
        more={
          rest.length > 0 && (
            <DropdownMenu>
              <DropdownMenuTrigger
                render={
                  <Button
                    variant="ghost"
                    size="icon"
                    // Closer to the last tab than the tabs are to each other, so three tabs and
                    // the button fit a phone's width.
                    className="-ms-4 -mt-1.5 shrink-0 text-muted-foreground hover:text-foreground"
                    aria-label={t("morePages")}
                  />
                }
              >
                <MoreHorizontalIcon className="size-5" />
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end" className="w-56 p-2">
                {rest.map((item) => (
                  <DropdownMenuItem
                    key={item.id}
                    className={cn(
                      "px-3 py-2",
                      item.keepCase ? "normal-case" : "lowercase"
                    )}
                    render={<Link href={item.href ?? ""} />}
                  >
                    {item.label}
                  </DropdownMenuItem>
                ))}
              </DropdownMenuContent>
            </DropdownMenu>
          )
        }
      />
      {open?.sub && (
        <SubPages label={open.label} items={open.sub} current={currentSub} />
      )}
    </div>
  )
}

/** The open page's own pages: the open one named in a full-width bar in the site's select look
 * (as MenuPill), opening a menu of links to them all, the open one checked. */
function SubPages({
  label,
  items,
  current,
}: {
  label: string
  items: NonNullable<SideMenuItem["sub"]>
  current?: string
}) {
  const chosen = items.find((item) => item.id === current) ?? items[0]
  // Named by the page and the open sub-page, so the visible text is in its name (WCAG 2.5.3).
  const labelId = useId()
  const valueId = useId()

  return (
    // Edge to edge of the screen: out of the page's side padding (`px-6`), the text kept in line
    // with the page by the pill's own padding.
    <nav aria-label={label} className="-mx-6">
      <DropdownMenu>
        <DropdownMenuTrigger
          aria-labelledby={`${labelId} ${valueId}`}
          // Square and straight under the row's line, so it reads as the row's continuation.
          className={cn(MENU_PILL_CLASS, "rounded-none")}
        >
          <span id={labelId} className="sr-only">
            {label}
          </span>
          <span
            id={valueId}
            className={cn(
              "truncate",
              chosen.keepCase ? "normal-case" : "lowercase"
            )}
          >
            {chosen.label}
          </span>
          <ChevronDownIcon aria-hidden className={MENU_PILL_CHEVRON_CLASS} />
        </DropdownMenuTrigger>
        <DropdownMenuContent align="end" className="max-h-80 w-72 p-2">
          {items.map((item) => (
            <DropdownMenuItem
              key={item.id}
              aria-current={item.id === chosen.id ? "page" : undefined}
              className={cn(
                "px-3 py-2 pe-8",
                item.keepCase ? "normal-case" : "lowercase"
              )}
              render={<Link href={item.href} />}
            >
              {item.label}
              {item.id === chosen.id && (
                <CheckIcon aria-hidden className="absolute end-2" />
              )}
            </DropdownMenuItem>
          ))}
        </DropdownMenuContent>
      </DropdownMenu>
    </nav>
  )
}
