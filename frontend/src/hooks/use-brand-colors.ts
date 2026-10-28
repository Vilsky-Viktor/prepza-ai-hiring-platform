"use client"

import { useSearchParams } from "next/navigation"
import { useTheme } from "next-themes"
import { useEffect } from "react"

import { brandStyle, pickTheme } from "@/lib/brand"
import { BRAND_FONTS } from "@/constants/brand-fonts"
import type { BrandColorSets, BrandStyle, Theme } from "@/types/company"

/** A company's colors, font and corner rounding over the whole page while it's open (a candidate's invitation, questions
 * and finished page), whatever the visitor's own theme: the set of the theme the address asks
 * for (`?theme=light`, `dark`, or `default`: the visitor's own; the SDK passes it so), else the
 * one its invite asked for through the API, else the visitor's own. prepza's again after. */
export function useBrandColors(
  sets: BrandColorSets | null | undefined,
  inviteTheme?: Theme | null,
  look?: BrandStyle | null
) {
  const asked = useSearchParams().get("theme")
  const { resolvedTheme } = useTheme()
  const theme = pickTheme(
    asked,
    inviteTheme,
    resolvedTheme === "dark" ? "dark" : "light"
  )
  const colors = sets?.[theme]
  const radius = look?.radius
  const buttonRadius = look?.button_radius
  const font = look ? BRAND_FONTS[look.font]?.family : undefined

  useEffect(() => {
    if (!colors) {
      return
    }

    const root = document.documentElement
    const style = {
      ...brandStyle(
        colors,
        radius === undefined || buttonRadius === undefined
          ? undefined
          : { radius, buttonRadius, font }
      ),
      "color-scheme": theme,
    }

    for (const [property, value] of Object.entries(style)) {
      root.style.setProperty(property, value)
    }

    return () => {
      for (const property of Object.keys(style)) {
        root.style.removeProperty(property)
      }
    }
  }, [colors, theme, radius, buttonRadius, font])

  return theme
}
