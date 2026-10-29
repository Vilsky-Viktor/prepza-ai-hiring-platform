"use client"

import { useTranslations } from "next-intl"

import { ChoiceOptions } from "@/features/company/components/choice-options"
import { Button } from "@/components/ui/button"
import { brandStyle } from "@/lib/brand"
import { BRAND_FONTS } from "@/config/brand-fonts"
import type { BrandColors, BrandStyle } from "@/types/company"

/** A candidate's pages in the company's colors, font and rounding, as they're picked: a rule, a question with a
 * picked answer, the start button and the finish dialog. */
export function BrandPreview({
  colors,
  look,
}: {
  colors: BrandColors
  look: BrandStyle
}) {
  const t = useTranslations("brand")
  const invite = useTranslations("invite")
  const session = useTranslations("session")

  return (
    <div
      style={brandStyle(colors, {
        radius: look.radius,
        buttonRadius: look.button_radius,
        font: BRAND_FONTS[look.font]?.family,
      })}
      aria-hidden
      inert
      className="space-y-5 rounded-2xl border bg-background p-6 font-sans text-foreground"
    >
      <h3 className="font-heading text-2xl font-medium">{t("sampleTitle")}</h3>
      <p className="flex gap-3 rounded-2xl bg-muted p-4 text-muted-foreground">
        <span className="font-medium text-primary">1.</span>
        {invite("pickOne")}
      </p>
      <div className="h-1.5 overflow-hidden rounded-full bg-muted">
        <div className="h-full w-2/5 bg-primary" />
      </div>
      <p className="rounded-xl bg-surface p-4 text-lg">{t("sampleQuestion")}</p>
      <ChoiceOptions
        options={t.raw("sampleOptions") as string[]}
        chosen={[0]}
        disabled
        onChoose={() => {}}
      />
      <Button className="h-12 px-6 text-base">{invite("start")}</Button>
      <div className="space-y-1 rounded-2xl bg-popover p-4 text-popover-foreground ring-1 ring-foreground/10">
        <p className="font-medium">{session("finishTitle")}</p>
        <p className="text-sm text-muted-foreground">{session("endsOne")}</p>
      </div>
    </div>
  )
}
