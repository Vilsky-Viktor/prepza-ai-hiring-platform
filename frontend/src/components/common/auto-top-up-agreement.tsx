"use client"

import { useTranslations } from "next-intl"

import { Checkbox } from "@/components/ui/checkbox"

/** The buyer's own agreement to an automatic top-up's terms, unticked until they tick it: the
 * amount each charge costs (plus tax), the balance that starts one, and that it charges until
 * they turn it off in the same dialog. */
export function AutoTopUpAgreement({
  amount,
  threshold,
  agreed,
  disabled,
  onChange,
}: {
  amount: string
  threshold: number
  agreed: boolean
  disabled: boolean
  onChange: (agreed: boolean) => void
}) {
  const t = useTranslations("autoTopUp")

  return (
    <label className="flex cursor-pointer items-start gap-3 text-sm">
      <Checkbox
        className="mt-0.5 size-5 shrink-0 [&_[data-slot=checkbox-indicator]>svg]:size-3.5"
        checked={agreed}
        disabled={disabled}
        data-testid="auto-top-up-agree"
        onCheckedChange={onChange}
      />
      <span>{t("agree", { amount, threshold })}</span>
    </label>
  )
}
