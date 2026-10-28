"use client"

import { useBrandColors } from "@/hooks/use-brand-colors"
import type { BrandColorSets, BrandStyle } from "@/types/company"

/** A server-rendered page in a company's colors: a member's preview of its invitation. */
export function BrandColorsOn({
  colors,
  look,
}: {
  colors: BrandColorSets | null
  look: BrandStyle | null
}) {
  useBrandColors(colors, null, look)

  return null
}
