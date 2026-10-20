"use client"

import { RepeatIcon, SquarePenIcon } from "lucide-react"
import { useRouter } from "next/navigation"
import { useLocale, useTranslations } from "next-intl"
import { useEffect, useRef, useState } from "react"
import { toast } from "sonner"

import { useAuth } from "@/components/auth-provider"
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
  DialogTrigger,
} from "@/components/ui/dialog"
import { apiErrorMessage, apiFetch } from "@/lib/api"
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
  const router = useRouter()
  const { user } = useAuth()
  const path = `/companies/companies/${companyId}/auto-top-up`
  const [setting, setSetting] = useState<AutoTopUp | null>(null)
  const [open, setOpen] = useState(false)
  const [product, setProduct] = useState("")
  const [threshold, setThreshold] = useState("")
  const [saving, setSaving] = useState(false)
  // The recheck after Paddle's checkout, stopped when the setting leaves the page.
  const recheck = useRef<number | undefined>(undefined)

  useEffect(() => {
    apiFetch<AutoTopUp>(path)
      .then(setSetting)
      .catch(() => {})
  }, [path])

  useEffect(() => () => clearTimeout(recheck.current), [])

  if (!setting?.offered || !user) {
    return null
  }

  const titles = Object.fromEntries(
    catalog.products.map((item) => [item.key, item.title])
  )
  // The candidates each amount buys, as billing's catalog says.
  const buys = Object.fromEntries(
    catalog.products.map((item) => [item.key, item.candidates])
  )
  const credits = (count: number) => count.toLocaleString(locale)

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

      await openCheckout(
        catalog,
        {
          priceId: saved.checkout.price_id,
          customData: saved.checkout.custom_data,
        },
        user!.email,
        () => {
          toast.success(t("turnedOn"))
          // Paddle confirms the subscription within seconds.
          recheck.current = window.setTimeout(() => {
            apiFetch<AutoTopUp>(path)
              .then(setSetting)
              .catch(() => {})
            router.refresh()
          }, 4000)
        },
        locale
      )
    } catch (error) {
      toast.error(apiErrorMessage(error, t("failed")))
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

  const summary =
    setting.on && setting.product && setting.threshold
      ? t("on", {
          amount: titles[setting.product] ?? setting.product,
          threshold: credits(setting.threshold),
        })
      : setting.waiting
        ? t("waiting")
        : null

  const set = setting.on || setting.waiting
  // Once on, saving needs a change; turning it on doesn't.
  const changed =
    !setting.on ||
    product !== setting.product ||
    Number(threshold) !== setting.threshold

  return (
    <Dialog open={open} onOpenChange={handleOpen}>
      {/* Off: a button that says what it does. On (or waiting for the card): the setting, with
          the app's edit icon to change it. */}
      {card ? (
        <div
          className="flex items-center gap-4 rounded-2xl border p-5 max-sm:flex-col max-sm:items-stretch"
          data-testid="auto-top-up"
        >
          <div className="min-w-0 flex-1 space-y-1">
            <p className="font-heading text-base font-medium lowercase">
              {t("title")}
              <span className="text-primary">.</span>
            </p>
            <p
              className="text-sm text-muted-foreground"
              data-testid={set ? "auto-top-up-on" : undefined}
            >
              {setting.on && setting.product && setting.threshold
                ? t("cardOn", {
                    amount: titles[setting.product] ?? setting.product,
                    threshold: credits(setting.threshold),
                  })
                : setting.waiting
                  ? t("cardWaiting")
                  : t("cardOff")}
            </p>
          </div>
          <DialogTrigger
            data-testid={set ? undefined : "set-up-auto-top-up"}
            render={
              <Button type="button" variant="outline" className="h-10 px-5" />
            }
          >
            {set ? t("changeShort") : t("setUpShort")}
          </DialogTrigger>
        </div>
      ) : summary ? (
        <p
          className="text-sm text-muted-foreground"
          data-testid="auto-top-up-on"
        >
          {summary}
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
      ) : (
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
      )}
      <DialogContent showCloseButton={false} className="sm:max-w-lg">
        <DialogHeader>
          <DialogTitle>{t("title")}</DialogTitle>
          <DialogDescription>{t("text")}</DialogDescription>
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
