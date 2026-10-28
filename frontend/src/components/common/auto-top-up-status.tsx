"use client"

import { cn } from "cn"
import { CreditCardIcon, RepeatIcon, SquarePenIcon } from "lucide-react"
import { useLocale, useTranslations } from "next-intl"
import type { ReactNode } from "react"

import { Button } from "@/components/ui/button"
import { DialogTrigger } from "@/components/ui/dialog"
import { formatDay, formatPrice } from "@/lib/format"
import { timeTag } from "@/lib/time-tag"
import type { AutoTopUp } from "@/types/billing"
import { CARD } from "@/config/cards"

type State = "off" | "on" | "waiting" | "paused"

// Each state's text, as a card and as a line.
const CARD_TEXTS = {
  off: "cardOff",
  on: "cardOn",
  waiting: "cardWaiting",
  paused: "cardPaused",
} as const
const LINE_TEXTS = {
  on: "on",
  waiting: "waiting",
  paused: "paused",
} as const

type Props = {
  setting: AutoTopUp
  titles: Record<string, string>
  card?: boolean
  updating: boolean
  onUpdateCard: () => void
}

function stateOf(setting: AutoTopUp): State {
  if (setting.paused) {
    return "paused"
  }

  if (setting.on && setting.product && setting.threshold) {
    return "on"
  }

  return setting.waiting ? "waiting" : "off"
}

/** The amount and level a running one is set to, and the new price billing announced with its
 * day, as written. */
function useValues(setting: AutoTopUp, titles: Record<string, string>) {
  const t = useTranslations("autoTopUp")
  const locale = useLocale()
  const values = {
    amount: titles[setting.product ?? ""] ?? setting.product ?? "",
    threshold: setting.threshold ?? 0,
  }
  const next =
    setting.next_price != null && setting.next_price_from && !setting.paused
      ? t.rich("nextPrice", {
          date: formatDay(setting.next_price_from, locale),
          amount: formatPrice(setting.next_price, setting.currency, locale),
          ...timeTag(setting.next_price_from),
        })
      : null

  return { values, next }
}

function UpdateCard({
  card,
  updating,
  onUpdateCard,
}: Omit<Props, "setting" | "titles">) {
  const t = useTranslations("autoTopUp")

  return (
    <Button
      type="button"
      variant="outline"
      size={card ? "default" : "sm"}
      className={card ? "h-10 px-5" : "h-8 px-3 text-sm"}
      disabled={updating}
      onClick={onUpdateCard}
      data-testid="update-card"
    >
      {!card && <CreditCardIcon data-icon="inline-start" />}
      {t("updateCard")}
    </Button>
  )
}

function NextPrice({
  text,
  className,
}: {
  text: ReactNode
  className?: string
}) {
  return (
    text && (
      <p
        className={cn("text-sm text-muted-foreground", className)}
        data-testid="next-price"
      >
        {text}
      </p>
    )
  )
}

/** In the top-up dialog: a card with its title, what it is now and its buttons. */
function StatusCard(props: Props) {
  const t = useTranslations("autoTopUp")
  const { setting, titles } = props
  const state = stateOf(setting)
  const { values, next } = useValues(setting, titles)
  const set = state !== "off"

  return (
    <div
      className={`flex items-center gap-4 ${CARD} max-sm:flex-col max-sm:items-stretch`}
      data-testid="auto-top-up"
      data-paused={setting.paused || undefined}
    >
      <div className="min-w-0 flex-1 space-y-1">
        <p className="font-heading text-base font-medium lowercase">
          {t("title")}
          <span className="text-primary">.</span>
        </p>
        <p
          className={cn(
            "text-sm",
            setting.paused ? "text-destructive" : "text-muted-foreground"
          )}
          data-testid={set ? "auto-top-up-on" : undefined}
        >
          {t(CARD_TEXTS[state], values)}
        </p>
        <NextPrice text={next} />
      </div>
      {setting.paused && <UpdateCard {...props} />}
      <DialogTrigger
        data-testid={set ? undefined : "set-up-auto-top-up"}
        render={
          <Button type="button" variant="outline" className="h-10 px-5" />
        }
      >
        {set ? t("changeShort") : t("setUpShort")}
      </DialogTrigger>
    </div>
  )
}

/** What an automatic top-up is now, beside the dialog that changes it: off, a button that says
 * what it does; on (or waiting for the card), the setting with the edit icon, and a new price
 * billing announced with its day; paused, why, with the button that updates the card. As a
 * `card`, it has a title and its button to set it up or change it. `titles` are the amounts as
 * written. */
export function AutoTopUpStatus(props: Props) {
  const t = useTranslations("autoTopUp")
  const { setting, titles } = props
  const state = stateOf(setting)
  const { values, next } = useValues(setting, titles)

  if (props.card) {
    return <StatusCard {...props} />
  }

  if (state === "off") {
    return (
      <DialogTrigger
        data-testid="set-up-auto-top-up"
        render={
          <Button
            type="button"
            variant="outline"
            size="sm"
            className="h-8 px-3 text-sm"
          />
        }
      >
        <RepeatIcon data-icon="inline-start" />
        {t("setUp")}
      </DialogTrigger>
    )
  }

  return (
    <div className="flex flex-wrap items-center gap-x-3 gap-y-2">
      <p
        className={cn(
          "text-sm",
          setting.paused ? "text-destructive" : "text-muted-foreground"
        )}
        data-testid="auto-top-up-on"
        data-paused={setting.paused || undefined}
      >
        {t(LINE_TEXTS[state], values)}
        <DialogTrigger
          render={
            <Button
              type="button"
              variant="ghost"
              size="icon-xs"
              className="-my-1 ms-1 align-middle text-muted-foreground hover:text-foreground"
              aria-label={t("change")}
            />
          }
        >
          <SquarePenIcon className="size-3.5" />
        </DialogTrigger>
      </p>
      {setting.paused && <UpdateCard {...props} />}
      <NextPrice text={next} className="basis-full" />
    </div>
  )
}
