"use client"

import { cn } from "cn"
import { MoreHorizontalIcon } from "lucide-react"
import Link from "next/link"
import { useTranslations } from "next-intl"

import type { SideMenuItem } from "@/components/side-menu"
import { TabNav } from "@/components/tab-nav"
import { Button } from "@/components/ui/button"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { splitPhoneTabs } from "@/lib/phone-tabs"

/** A page menu on phones and narrow screens: the site's tabs, the first three in the row and
 * the others, in their order, in a menu under a "…" button; an open page from that menu takes
 * the third place. A page with pages of its own (`sub`) shows them as pills under the row. */
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
        // The open page's own pages: pills on a band of the row's line colour, softened,
        // hanging from that line, so they read as part of the row; the open one in the page's
        // colour.
        <nav
          aria-label={open.label}
          className="flex gap-2 rounded-b-2xl bg-border/50 p-2"
        >
          {open.sub.map((item) => (
            <Link
              key={item.id}
              href={item.href}
              aria-current={item.id === currentSub ? "page" : undefined}
              className={cn(
                "rounded-full px-4 py-1.5 text-base lowercase transition-colors",
                item.id === currentSub
                  ? "bg-background text-foreground"
                  : "text-muted-foreground hover:text-foreground"
              )}
            >
              {item.label}
            </Link>
          ))}
        </nav>
      )}
    </div>
  )
}
