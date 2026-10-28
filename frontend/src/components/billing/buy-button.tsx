"use client"

import { cn } from "cn"
import { useLocale, useTranslations } from "next-intl"
import { useTheme } from "next-themes"
import { useState } from "react"
import { toast } from "sonner"

import { useSignIn } from "@/components/sign-in-dialog"
import { useAuth } from "@/components/auth-provider"
import { Button } from "@/components/ui/button"
import { apiFetch } from "@/lib/api"
import { openCheckout } from "@/lib/paddle"
import type { Catalog, CheckoutData } from "@/types/billing"

/** Buys a top-up of `candidates` for `companyId`, at the price billing sets for the count. */
export function BuyButton({
  catalog,
  candidates,
  onSale,
  companyId,
  label,
  variant = "default",
  className,
  onOpened,
}: {
  catalog: Catalog
  candidates: number
  // False while its price isn't on sale yet.
  onSale: boolean
  companyId: string
  label?: string
  variant?: "default" | "outline"
  className?: string
  // Called once the checkout is shown (the top-up dialog closes then).
  onOpened?: () => void
}) {
  const t = useTranslations("billing")
  const locale = useLocale()
  const signIn = useSignIn()
  const { resolvedTheme } = useTheme()
  const { user } = useAuth()
  const [opening, setOpening] = useState(false)

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
      // It opens over this page; a completed payment shows the success dialog here, a failed
      // one the failure dialog.
      await openCheckout({
        catalog,
        checkout: { transactionId },
        email: user.email,
        theme: resolvedTheme === "dark" ? "dark" : "light",
        paid: "top_up",
        locale,
        companyId,
      })
      onOpened?.()
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
