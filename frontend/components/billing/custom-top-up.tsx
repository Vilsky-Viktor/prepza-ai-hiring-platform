"use client"

import { ChevronDownIcon, ChevronRightIcon } from "lucide-react"
import { useLocale, useTranslations } from "next-intl"
import { cn } from "cn"
import { Fragment, useState } from "react"

import { BuyButton } from "@/components/billing/buy-button"
import { Slider } from "@/components/ui/slider"
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip"
import { compactNumber, formatPrice } from "@/lib/format"
import { AREA_STEPS, candidatesAt, customTopUp, positionOf } from "@/lib/top-up"
import type { Catalog } from "@/types/billing"

// Keys that move the slider by whole candidates, not by its steps; right to left, the arrows'
// sides swap, as the slider is mirrored.
const KEY_STEPS: Record<string, number> = {
  ArrowRight: 1,
  ArrowUp: 1,
  ArrowLeft: -1,
  ArrowDown: -1,
  PageUp: 10,
  PageDown: -10,
}

/** A top-up of any number of candidates: a slider with one area per price, what it costs as
 * price, credits and candidates, and the button that opens the checkout. */
export function CustomTopUp({
  catalog,
  companyId,
  onOpened,
}: {
  catalog: Catalog
  companyId: string
  // Called once the checkout is shown.
  onOpened?: () => void
}) {
  const t = useTranslations("billing")
  const locale = useLocale()
  const { custom } = catalog
  const [count, setCount] = useState(custom.min_candidates)
  const bought = customTopUp(custom, count)
  const price = (cents: number) => formatPrice(cents, catalog.currency, locale)
  const number = (value: number) => value.toLocaleString(locale)

  function onKeyDown(event: React.KeyboardEvent<HTMLElement>) {
    const mirrored =
      ["ArrowLeft", "ArrowRight"].includes(event.key) &&
      getComputedStyle(event.currentTarget).direction === "rtl"
    const step =
      KEY_STEPS[event.key] === undefined
        ? undefined
        : KEY_STEPS[event.key] * (mirrored ? -1 : 1)
    const edge =
      event.key === "Home"
        ? custom.min_candidates
        : event.key === "End"
          ? custom.max_candidates
          : null

    if (step === undefined && edge === null) {
      return
    }

    // Stops the slider's own step, so a key moves one candidate in every area.
    event.preventDefault()
    setCount(
      edge ??
        Math.min(
          Math.max(count + (step ?? 0), custom.min_candidates),
          custom.max_candidates
        )
    )
  }

  const credits = bought.candidates * catalog.candidate_credits
  // Credits and candidates short, as the balance is ("1.5K"), whole on hover.
  const cards = [
    { value: price(bought.cents) },
    {
      value: compactNumber(credits, locale),
      word: t("creditsWord", { count: credits }),
      full: t("credits", { count: credits }),
    },
    {
      value: compactNumber(bought.candidates, locale),
      word: t("candidatesWord", { count: bought.candidates }),
      full: t("candidates", { count: bought.candidates }),
    },
  ]

  return (
    <div className="space-y-6">
      {/* Room above the track for the number over the knob. */}
      <div className="pt-9">
        <Slider
          min={0}
          max={custom.tiers.length * AREA_STEPS}
          value={positionOf(custom, count)}
          onValueChange={(value) => setCount(candidatesAt(custom, value))}
          marks={custom.tiers.slice(1).map((tier, index) => (
            <span
              key={tier.from_candidates}
              aria-hidden
              className="absolute top-1/2 h-4 w-0.5 -translate-x-1/2 -translate-y-1/2 rounded-full bg-border rtl:translate-x-1/2"
              style={{
                insetInlineStart: `${((index + 1) / custom.tiers.length) * 100}%`,
              }}
            />
          ))}
          thumb={{
            "aria-label": t("howMany"),
            getAriaValueText: () =>
              `${t("candidates", { count })}, ${price(bought.cents)}`,
            onKeyDown,
            // The slider's own count, over the knob, moving and growing with it.
            children: (
              <span
                aria-hidden
                className="pointer-events-none absolute bottom-full left-1/2 mb-2 -translate-x-1/2 rounded-full bg-primary px-2 py-0.5 text-xs font-medium whitespace-nowrap text-primary-foreground tabular-nums"
                data-testid="custom-count"
              >
                {number(count)}
                {/* Its pointer toward the knob. */}
                <span className="absolute top-full left-1/2 -translate-x-1/2 border-x-[6px] border-t-[6px] border-x-transparent border-t-primary" />
              </span>
            ),
          }}
        />
        <div
          className="-mt-1 grid text-center text-xs text-muted-foreground tabular-nums"
          style={{
            gridTemplateColumns: `repeat(${custom.tiers.length}, minmax(0, 1fr))`,
          }}
        >
          {custom.tiers.map((tier) => (
            <span
              key={tier.from_candidates}
              className="[overflow-wrap:anywhere]"
            >
              {t.rich("perCandidate", {
                price: price(tier.cents),
                // "/candidate" a step smaller than the price.
                unit: (chunks) => (
                  <span className="text-[0.625rem]">{chunks}</span>
                ),
              })}
            </span>
          ))}
        </div>
      </div>
      <div className="space-y-2">
        <div
          className="flex flex-col items-stretch gap-2 sm:flex-row sm:items-center"
          data-testid="custom-quote"
        >
          {cards.map((card, index) => (
            <Fragment key={index}>
              {index > 0 && (
                <>
                  <ChevronRightIcon
                    aria-hidden
                    className="size-7 shrink-0 self-center text-muted-foreground max-sm:hidden rtl:-scale-x-100"
                  />
                  <ChevronDownIcon
                    aria-hidden
                    className="size-7 shrink-0 self-center text-muted-foreground sm:hidden"
                  />
                </>
              )}
              <p className="flex-1 rounded-2xl bg-muted px-4 py-3 text-center">
                {card.full ? (
                  <Tooltip>
                    <TooltipTrigger
                      render={
                        <span className="font-heading text-2xl font-medium tabular-nums" />
                      }
                    >
                      {card.value}
                    </TooltipTrigger>
                    <TooltipContent>{card.full}</TooltipContent>
                  </Tooltip>
                ) : (
                  <span className="font-heading text-2xl font-medium tabular-nums">
                    {card.value}
                  </span>
                )}{" "}
                {card.word && (
                  <span className="text-sm text-muted-foreground">
                    {card.word}
                  </span>
                )}
              </p>
            </Fragment>
          ))}
        </div>
        {/* Its line is always there, so nothing moves when it shows. */}
        <p
          className={cn(
            "h-5 text-center text-sm text-muted-foreground",
            !bought.upgraded && "invisible"
          )}
          data-testid={bought.upgraded ? "custom-upgraded" : undefined}
        >
          {bought.upgraded &&
            t("upgraded", { count: number(bought.candidates) })}
        </p>
      </div>
      {/* A little closer to the cards than the dialog's other gaps. */}
      <div className="-mt-2 flex justify-center">
        <BuyButton
          catalog={catalog}
          candidates={bought.candidates}
          onSale={bought.onSale}
          companyId={companyId}
          className="h-14 px-12 text-lg"
          onOpened={onOpened}
        />
      </div>
    </div>
  )
}
