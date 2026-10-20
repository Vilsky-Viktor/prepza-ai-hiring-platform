"use client"

import { cn } from "cn"
import { useRouter } from "next/navigation"
import { useTranslations } from "next-intl"
import { useEffect, useRef, useState } from "react"
import { toast } from "sonner"

import { useSignIn } from "@/components/sign-in-dialog"
import { useAuth } from "@/components/auth-provider"
import { Button } from "@/components/ui/button"
import { apiFetch } from "@/lib/api"
import { openCheckout } from "@/lib/paddle"
import type { Catalog, CheckoutData } from "@/types/billing"

// When to look for the new balance after a payment, in seconds.
const RECHECK_SECONDS = [2, 5, 10, 20, 40]

/** Buys a top-up of `candidates` for `companyId`, at the price billing sets for the count. */
export function BuyButton({
  catalog,
  candidates,
  onSale,
  companyId,
  label,
  variant = "default",
  className,
}: {
  catalog: Catalog
  candidates: number
  // False while its price isn't on sale yet.
  onSale: boolean
  companyId: string
  label?: string
  variant?: "default" | "outline"
  className?: string
}) {
  const t = useTranslations("billing")
  const signIn = useSignIn()
  const router = useRouter()
  const { user } = useAuth()
  const [opening, setOpening] = useState(false)
  // The balance rechecks after a payment, stopped when the button leaves the page.
  const rechecks = useRef<number[]>([])

  useEffect(() => () => rechecks.current.forEach(clearTimeout), [])

  if (!onSale) {
    return (
      <Button
        variant="outline"
        className={cn("h-12 px-6 text-base", className)}
        disabled
      >
        {label ?? t("topUp")}
      </Button>
    )
  }

  async function buy() {
    if (!user) {
      await signIn()

      return
    }

    setOpening(true)

    try {
      // The backend makes the checkout, with its price and whose wallet it pays into.
      const { transaction_id: transactionId } = await apiFetch<CheckoutData>(
        `/companies/companies/${companyId}/billing/checkout`,
        { method: "POST", body: JSON.stringify({ candidates }) }
      )
      await openCheckout(catalog, { transactionId }, user.email, () => {
        toast.success(t("paid"))
        // Paddle's webhook usually lands within seconds, sometimes later: look again a few
        // times, and the balances count up when it has.
        rechecks.current = RECHECK_SECONDS.map((seconds) =>
          window.setTimeout(() => router.refresh(), seconds * 1000)
        )
      })
    } catch {
      toast.error(t("checkoutFailed"))
    } finally {
      setOpening(false)
    }
  }

  return (
    <Button
      variant={variant}
      className={cn("h-12 px-6 text-base", className)}
      disabled={opening}
      onClick={buy}
    >
      {label ?? t("topUp")}
    </Button>
  )
}
