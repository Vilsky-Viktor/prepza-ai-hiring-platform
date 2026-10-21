"use client"

import { useLocale, useTranslations } from "next-intl"
import { useTheme } from "next-themes"
import { useEffect, useState } from "react"
import { toast } from "sonner"

import { useAuth } from "@/components/auth-provider"
import { AutoTopUpStatus } from "@/components/billing/auto-top-up-status"
import { Dotted } from "@/components/dot"
import { PillSelect } from "@/components/pill-select"
import { Button } from "@/components/ui/button"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { BILLING_REFRESHED } from "@/constants/billing"
import { apiErrorMessage, apiFetch, serviceRefusal } from "@/lib/api"
import { formatPrice } from "@/lib/format"
import { openCheckout } from "@/lib/paddle"
import type { AutoTopUp, Catalog } from "@/types/billing"

/** A wallet's automatic top-up: what it is now, and a dialog to turn it on, change or turn
 * off. Turning it on the first time opens Paddle's checkout to save the card. As a `card`, it
 * has a title, what it does or is set to, and a button to set it up or change it. */
export function AutoTopUpSetting({
  catalog,
  companyId,
  card,
}: {
  catalog: Catalog
  companyId: string
  card?: boolean
}) {
  const t = useTranslations("autoTopUp")
  const common = useTranslations("common")
  const billing = useTranslations("billing")
  const locale = useLocale()
  const { resolvedTheme } = useTheme()
  const { user } = useAuth()
  const path = `/companies/companies/${companyId}/auto-top-up`
  const [setting, setSetting] = useState<AutoTopUp | null>(null)
  const [open, setOpen] = useState(false)
  const [product, setProduct] = useState("")
  const [threshold, setThreshold] = useState("")
  const [saving, setSaving] = useState(false)

  // Read again as the page refreshes after a payment: a card update resumes it once Paddle's
  // web hook has come.
  useEffect(() => {
    const load = () =>
      apiFetch<AutoTopUp>(path)
        .then(setSetting)
        .catch(() => {})
    load()
    window.addEventListener(BILLING_REFRESHED, load)

    return () => window.removeEventListener(BILLING_REFRESHED, load)
  }, [path])

  if (!setting?.offered || !user) {
    return null
  }

  // Each amount in the currency Paddle charges it in, as billing says.
  const titles = Object.fromEntries(
    Object.entries(setting.prices).map(([key, cents]) => [
      key,
      formatPrice(cents, setting.currency, locale),
    ])
  )
  // The candidates each amount buys, as billing's catalog says.
  const buys = Object.fromEntries(
    catalog.products.map((item) => [item.key, item.candidates])
  )
  const credits = (count: number) => count.toLocaleString(locale)
  const checkoutFor = (transactionId: string) => ({
    catalog,
    checkout: { transactionId },
    email: user!.email,
    theme: resolvedTheme === "dark" ? ("dark" as const) : ("light" as const),
    locale,
    companyId,
  })

  function handleOpen(next: boolean) {
    if (saving || !setting) {
      return
    }

    setOpen(next)
    setProduct(setting.product ?? setting.products[0] ?? "")
    setThreshold(String(setting.threshold ?? setting.thresholds[0] ?? ""))
  }

  async function save(event: React.FormEvent) {
    event.preventDefault()
    setSaving(true)

    try {
      const saved = await apiFetch<AutoTopUp>(path, {
        method: "PUT",
        body: JSON.stringify({ product, threshold: Number(threshold) }),
      })
      setSetting(saved)
      setOpen(false)

      if (!saved.checkout) {
        toast.success(t("saved"))

        return
      }

      // It opens over this page; a completed payment shows the success dialog here, a failed
      // one the failure dialog.
      await openCheckout({
        ...checkoutFor(saved.checkout.transaction_id),
        paid: "auto_top_up",
      })
    } catch (error) {
      // Billing's refusal says why: someone else's card pays for it (403).
      toast.error(
        serviceRefusal(error, [403]) ?? apiErrorMessage(error, t("failed"))
      )
    } finally {
      setSaving(false)
    }
  }

  // Paddle's checkout that saves a new card for it; a paused one starts again once saved.
  async function updateCard() {
    setSaving(true)

    try {
      const { transaction_id } = await apiFetch<{ transaction_id: string }>(
        `${path}/card`,
        { method: "POST" }
      )
      await openCheckout({ ...checkoutFor(transaction_id), paid: "card" })
    } catch (error) {
      // Billing's refusal says why: someone else's card pays for it (403), or it isn't on (409).
      toast.error(
        serviceRefusal(error, [403, 409]) ??
          apiErrorMessage(error, t("updateCardFailed"))
      )
    } finally {
      setSaving(false)
    }
  }

  async function turnOff() {
    setSaving(true)

    try {
      await apiFetch(path, { method: "DELETE" })
      setSetting(await apiFetch<AutoTopUp>(path))
      setOpen(false)
      toast.success(t("turnedOff"))
    } catch (error) {
      toast.error(apiErrorMessage(error, t("failed")))
    } finally {
      setSaving(false)
    }
  }

  const set = setting.on || setting.waiting
  // Once on, saving needs a change; turning it on doesn't.
  const changed =
    !setting.on ||
    product !== setting.product ||
    Number(threshold) !== setting.threshold

  return (
    <Dialog open={open} onOpenChange={handleOpen}>
      <AutoTopUpStatus
        setting={setting}
        titles={titles}
        card={card}
        updating={saving}
        onUpdateCard={updateCard}
      />
      <DialogContent showCloseButton={false} className="sm:max-w-lg">
        <DialogHeader>
          <DialogTitle>{t("title")}</DialogTitle>
          <DialogDescription>
            {t("text")} {billing("taxes")}
          </DialogDescription>
        </DialogHeader>
        <form id="auto-top-up-form" onSubmit={save} className="space-y-4">
          <PillSelect
            label={t("amount")}
            value={product}
            onChange={setProduct}
            options={setting.products.map((key) => ({
              value: key,
              label: titles[key] ?? key,
              note: billing("candidates", { count: buys[key] ?? 0 }),
              // The pill: the amount and, smaller, the candidates it buys.
              display: (
                <Dotted
                  items={[
                    titles[key] ?? key,
                    <span
                      key="candidates"
                      className="text-sm text-muted-foreground"
                    >
                      {billing("candidates", { count: buys[key] ?? 0 })}
                    </span>,
                  ]}
                />
              ),
            }))}
          />
          <PillSelect
            label={t("when")}
            value={threshold}
            onChange={setThreshold}
            options={setting.thresholds.map((value) => ({
              value: String(value),
              label: t("level", { threshold: credits(value) }),
            }))}
          />
        </form>
        <DialogFooter>
          {set && (
            <Button
              variant="secondary"
              className="h-10 px-5 text-base sm:me-auto"
              disabled={saving}
              onClick={turnOff}
            >
              {t("turnOff")}
            </Button>
          )}
          <Button
            variant="outline"
            className="h-10 px-5 text-base"
            disabled={saving}
            onClick={() => setOpen(false)}
          >
            {common("close")}
          </Button>
          <Button
            type="submit"
            form="auto-top-up-form"
            className="h-10 px-5 text-base"
            disabled={saving || !product || !threshold || !changed}
          >
            {setting.on ? t("save") : t("turnOn")}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
