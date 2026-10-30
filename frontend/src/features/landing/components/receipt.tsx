"use client"

import { cn } from "cn"
import { UserRoundIcon } from "lucide-react"

import { KeepAcronyms } from "@/components/common/keep-acronyms"
import { FREE_LINES, RECEIPT_STEPS } from "@/config/free-to-start-demo"
import { countedAt, useDemoSteps } from "@/hooks/use-demo-steps"

// A line not printed yet keeps its room, so the receipt doesn't grow as it prints.
const PRINTED =
  "animate-in duration-300 fade-in slide-in-from-top-1 motion-reduce:animate-none"

/** A receipt for a whole interview: its free lines print one by one as it comes into view,
 * then the one paid line, the candidates who answered, and the total changes to its price.
 * With reduced motion, the complete receipt. */
export function Receipt({
  free,
  zero,
  paid,
  paidAmount,
  totalLabel,
  perCandidate,
}: {
  free: Record<(typeof FREE_LINES)[number], string>
  zero: string
  paid: string
  paidAmount: string
  totalLabel: string
  perCandidate: string
}) {
  const { ref, index, n } = useDemoSteps<HTMLDivElement>(RECEIPT_STEPS)
  const printed = countedAt(
    RECEIPT_STEPS,
    { index, n },
    "free",
    FREE_LINES.length
  )
  const landed = RECEIPT_STEPS[index].name === "paid"

  return (
    <div
      ref={ref}
      aria-hidden
      data-testid="receipt"
      className="flex w-full max-w-md flex-col justify-between rounded-xl bg-surface p-7 text-base sm:p-9"
    >
      <ul className="space-y-2.5">
        {FREE_LINES.map((key, at) => (
          <ReceiptLine
            key={key}
            label={<KeepAcronyms text={free[key]} />}
            amount={zero}
            className={at < printed ? PRINTED : "invisible"}
          />
        ))}
        <ReceiptLine
          label={
            <span className="flex items-center gap-2">
              <span className="flex size-6 shrink-0 items-center justify-center rounded-full bg-background">
                <UserRoundIcon className="size-4 text-primary" />
              </span>
              {paid}
            </span>
          }
          amount={paidAmount}
          className={cn(
            "pt-1 font-medium text-primary",
            landed ? PRINTED : "invisible"
          )}
        />
      </ul>
      <div className="mt-4 flex items-baseline justify-between gap-3 border-t border-foreground/15 pt-4">
        <span className="font-heading text-lg font-medium lowercase">
          {totalLabel}
        </span>
        <span className="text-end">
          <span
            data-testid="receipt-total"
            className="font-heading text-2xl font-medium tabular-nums"
          >
            {landed ? paidAmount : zero}
          </span>
          <span
            className={cn(
              "block text-xs text-muted-foreground",
              !landed && "invisible"
            )}
          >
            {perCandidate}
          </span>
        </span>
      </div>
    </div>
  )
}

/** A receipt line: what it is, a dotted leader and its amount at the end. */
function ReceiptLine({
  label,
  amount,
  className,
}: {
  label: React.ReactNode
  amount: string
  className?: string
}) {
  return (
    <li className={cn("flex items-end gap-2 lowercase", className)}>
      <span className="min-w-0">{label}</span>
      <span className="mb-1 min-w-4 flex-1 border-b border-dotted border-current opacity-40" />
      <span className="shrink-0 tabular-nums">{amount}</span>
    </li>
  )
}
