"use client"

import { useTranslations } from "next-intl"
import { useState } from "react"

import { PillSelect } from "@/components/common/pill-select"
import { FloatingInput } from "@/components/ui/floating-field"
import { BRAND_FONTS } from "@/config/brand-fonts"
import type { BrandStyle } from "@/types/company"

// The rounding companies takes, in px.
const MAX_RADIUS = 24

type Props = { look: BrandStyle; onChange: (look: BrandStyle) => void }

/** The titles' and the text's fonts on the company's candidates' pages, the same in both
 * themes, each picked from the same fonts, by name. */
export function BrandFontFields({ look, onChange }: Props) {
  const t = useTranslations("brand")
  const options = Object.entries(BRAND_FONTS)
    .map(([value, font]) => ({
      value,
      label: font.label,
      fontFamily: font.family,
    }))
    .sort((a, b) => a.label.localeCompare(b.label))

  return (
    <>
      {(["heading_font", "text_font"] as const).map((key) => (
        <PillSelect
          key={key}
          label={t(key === "heading_font" ? "headingFont" : "textFont")}
          value={look[key]}
          options={options}
          onChange={(font) =>
            onChange({ ...look, [key]: font as BrandStyle[typeof key] })
          }
          pillClassName="w-72 justify-between"
        />
      ))}
    </>
  )
}

/** How round the cards' and buttons' corners are, the same in both themes. A rounding counts
 * once it's a whole number within bounds. */
export function BrandRoundingFields({ look, onChange }: Props) {
  const t = useTranslations("brand")

  return (
    <>
      <RadiusField
        label={t("radius")}
        value={look.radius}
        onChange={(radius) => onChange({ ...look, radius })}
      />
      <RadiusField
        label={t("buttonRadius")}
        value={look.button_radius}
        onChange={(button_radius) => onChange({ ...look, button_radius })}
      />
    </>
  )
}

function RadiusField({
  label,
  value,
  onChange,
}: {
  label: string
  value: number
  onChange: (value: number) => void
}) {
  const [typed, setTyped] = useState<string | null>(null)

  return (
    // The site's field, its name raised on its edge and the unit inside it.
    <FloatingInput
      label={label}
      type="number"
      min={0}
      max={MAX_RADIUS}
      suffix="px"
      value={typed ?? String(value)}
      boxClassName="w-40"
      onChange={(event) => {
        const next = Number(event.target.value)
        setTyped(event.target.value)

        if (
          event.target.value !== "" &&
          Number.isInteger(next) &&
          next >= 0 &&
          next <= MAX_RADIUS
        ) {
          onChange(next)
        }
      }}
      onBlur={() => setTyped(null)}
    />
  )
}
