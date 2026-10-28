"use client"

import { useTranslations } from "next-intl"
import { useState } from "react"

import { PillSelect } from "@/components/pill-select"
import { FloatingInput } from "@/components/ui/floating-field"
import { BRAND_FONTS } from "@/config/brand-fonts"
import type { BrandStyle } from "@/types/company"

// The rounding companies takes, in px.
const MAX_RADIUS = 24

type Props = { look: BrandStyle; onChange: (look: BrandStyle) => void }

/** The font of all the text on the company's candidates' pages, the same in both themes. */
export function BrandFontField({ look, onChange }: Props) {
  const t = useTranslations("brand")

  return (
    <PillSelect
      label={t("font")}
      value={look.font}
      options={Object.entries(BRAND_FONTS)
        .map(([value, font]) => ({
          value,
          label: font.label,
          fontFamily: font.family ?? "var(--font-poppins)",
        }))
        .sort((a, b) =>
          a.value === "poppins_geist" || b.value === "poppins_geist"
            ? Number(b.value === "poppins_geist") -
              Number(a.value === "poppins_geist")
            : a.label.localeCompare(b.label)
        )}
      onChange={(font) =>
        onChange({ ...look, font: font as BrandStyle["font"] })
      }
      pillClassName="w-72 justify-between"
    />
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
