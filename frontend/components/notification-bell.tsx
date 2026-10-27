"use client"

import { cn } from "cn"
import { BellIcon } from "lucide-react"
import Link from "next/link"
import { useFormatter, useLocale, useNow, useTranslations } from "next-intl"
import { useCallback, useEffect, useState } from "react"

import { useAuth } from "@/components/auth-provider"
import { Button } from "@/components/ui/button"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import {
  COMPANIES_CHANGED,
  MAX_BADGE_COUNT,
  NOTIFICATION_DEFAULTS,
  NOTIFICATION_LOOKS,
} from "@/constants/notifications"
import { ROUND_ICON_BUTTON } from "@/constants/buttons"
import { apiFetch } from "@/lib/api"
import { bdi, bdiText } from "@/lib/bidi"
import { formatDay, formatPercent, formatPrice } from "@/lib/format"
import { hasMessage } from "@/lib/messages"
import { watchNotifications } from "@/lib/notifications"
import { timeTag } from "@/lib/time-tag"
import type { AppNotification, NotificationFeed } from "@/types/notifications"

/** An automatic top-up's price change as the bell writes it: what it costs and will cost. */
function prices(
  data: Record<string, string | number | undefined>,
  locale: string
) {
  const money = (cents: unknown) =>
    typeof cents === "number" && typeof data.currency === "string"
      ? formatPrice(cents, data.currency, locale)
      : ""

  return { price: money(data.price), newPrice: money(data.new_price) }
}

/** One notification's text: its kind's message, filled with what the service sent. Missing
 * values become "none", which the messages' selects read as "leave it out". */
function useNotificationText() {
  const t = useTranslations("notifications.kinds")
  const common = useTranslations("common")
  const locale = useLocale()

  return (item: AppNotification) => {
    const data = item.data as Record<string, string | number | undefined>
    // The values the service sent, the others as NOTIFICATION_DEFAULTS has them.
    const given = Object.entries(data).filter(
      ([key, value]) => key in NOTIFICATION_DEFAULTS && value != null
    )
    const values = {
      ...NOTIFICATION_DEFAULTS,
      ...Object.fromEntries(given),
      // "Name (email)" once the candidate's name is known.
      email: data.candidate_name
        ? common.markup("nameWithEmail", {
            name: data.candidate_name,
            email: data.email ?? "",
            ...bdiText,
          })
        : (data.email ?? ""),
      // How many came together, for the kinds the service groups.
      count: typeof data.count === "number" ? data.count : 1,
      credits: typeof data.credits === "number" ? data.credits : 0,
      // A finished candidate's grade, as the language writes a percentage.
      grade:
        typeof data.grade === "number"
          ? formatPercent(data.grade, locale)
          : NOTIFICATION_DEFAULTS.grade,
      // The day a legal document's new version applies, or an automatic top-up's new price.
      date: typeof data.date === "string" ? formatDay(data.date, locale) : "",
      // An automatic top-up's price and its new one, in their currency.
      ...prices(data, locale),
    }

    return hasMessage(t, item.kind)
      ? t.rich(item.kind, {
          ...values,
          ...bdi,
          ...timeTag(typeof data.date === "string" ? data.date : ""),
        })
      : null
  }
}

/** The bell next to the account menu: the latest notifications, live, with a count of those
 * not yet seen. Opening it counts them as seen. */
export function NotificationBell() {
  const t = useTranslations("notifications")
  const { user } = useAuth()
  const format = useFormatter()
  // Re-renders each minute, so "2 minutes ago" keeps up.
  const now = useNow({ updateInterval: 60000 })
  const text = useNotificationText()
  const [feed, setFeed] = useState<NotificationFeed | null>(null)

  // Bumped when the user joins a company: the stream starts again with their companies fresh.
  const [joined, setJoined] = useState(0)
  const load = useCallback((fresh = false) => {
    apiFetch<NotificationFeed>(`/notifications/me${fresh ? "?fresh=true" : ""}`)
      .then(setFeed)
      .catch(() => {})
  }, [])

  useEffect(() => {
    const changed = () => setJoined((count) => count + 1)
    window.addEventListener(COMPANIES_CHANGED, changed)

    return () => window.removeEventListener(COMPANIES_CHANGED, changed)
  }, [])

  // Live while signed in: the stream says when something new came, and each (re)connect
  // reloads, so nothing that came while it was down is missed.
  useEffect(() => {
    if (!user) {
      return
    }

    const controller = new AbortController()
    const fresh = joined > 0
    void watchNotifications(
      controller.signal,
      () => load(fresh),
      () => load(),
      fresh
    )

    return () => controller.abort()
  }, [user, load, joined])

  if (!user || feed === null) {
    return null
  }

  const { items, unread } = feed

  function open(next: boolean) {
    if (!next || unread === 0) {
      return
    }

    setFeed((current) => current && { ...current, unread: 0 })
    apiFetch("/notifications/me/seen", { method: "POST" }).catch(() => {})
  }

  return (
    <DropdownMenu onOpenChange={open}>
      <DropdownMenuTrigger
        data-testid="notifications"
        render={
          <Button
            variant="ghost"
            size="icon"
            className={cn("relative", ROUND_ICON_BUTTON)}
            aria-label={
              unread > 0 ? t("unread", { count: unread }) : t("title")
            }
          />
        }
      >
        {/* It keeps swinging, every 4 s, while anything is unread (the owner's exception to
            WCAG 2.2.2; still with reduced motion). */}
        <BellIcon
          className={cn(
            "size-5 origin-top",
            unread > 0 && "animate-[bell-ring_4s_ease-in-out_infinite]"
          )}
        />
        {unread > 0 && (
          <span className="absolute -end-0.5 -top-0.5 flex h-4 min-w-4 items-center justify-center rounded-full bg-destructive px-1 text-[10px] leading-none font-medium text-white tabular-nums">
            {unread > MAX_BADGE_COUNT ? `${MAX_BADGE_COUNT}+` : unread}
          </span>
        )}
      </DropdownMenuTrigger>
      {/* At most about four notifications tall, never most of the screen; the rest scrolls,
          with a thin, quiet scrollbar. */}
      <DropdownMenuContent
        align="end"
        className="max-h-[min(26rem,70vh)] w-80 px-0 py-2"
      >
        {items.length === 0 && (
          <p className="px-3 py-6 text-center text-sm text-muted-foreground">
            {t("empty")}
          </p>
        )}
        {items.map((item) => {
          const look = NOTIFICATION_LOOKS[item.kind]
          const message = text(item)

          // A kind this page doesn't know yet (a newer service) isn't shown.
          if (!look || !message) {
            return null
          }

          return (
            <DropdownMenuItem
              key={item.id}
              className="relative items-start gap-3 rounded-none py-2.5 ps-9 pe-4 whitespace-normal normal-case"
              render={<Link href={item.link} />}
              // An alert (a problem to act on), its sign in red; others in the brand colour.
              data-alert={look.alert || undefined}
            >
              {/* The kind's sign, large and half transparent (full on hover), running a little
                  under the dropdown's start border (its scroll box clips it). Items run from
                  border to border. */}
              <look.icon
                aria-hidden
                className="absolute -start-2 top-2 size-8 shrink-0 opacity-50 transition-opacity group-hover/dropdown-menu-item:opacity-100 group-focus/dropdown-menu-item:opacity-100"
                // Its own colour always. The item's highlight recolours every element inside it,
                // the icon's lines too (they draw in currentColor), so the lines get the colour
                // as their stroke, which they inherit and the highlight doesn't touch.
                style={{
                  stroke: look.alert ? "var(--destructive)" : "var(--primary)",
                }}
              />
              <span className="min-w-0 space-y-1">
                <span className="block text-sm leading-snug">{message}</span>
                <time
                  dateTime={item.created_at}
                  className="block text-xs text-muted-foreground"
                >
                  {format.relativeTime(new Date(item.created_at), now)}
                </time>
              </span>
            </DropdownMenuItem>
          )
        })}
      </DropdownMenuContent>
    </DropdownMenu>
  )
}
