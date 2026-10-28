import { BRAND_VARIABLES } from "@/config/brand"
import type { BrandColors, Theme } from "@/types/company"

/** A company's colors, font and corner rounding (px: cards' and buttons', as drawn: cards are
 * rounded-xl, 1.4 times the theme's --radius, which the other corners scale from) as the theme
 * variables they set: on an element's style, everything inside takes them. A font family replaces both
 * of the site's, so it's all the text's; none keeps prepza's pair. */
export function brandStyle(
  colors: BrandColors,
  look?: { radius: number; buttonRadius: number; font?: string }
): Record<string, string> {
  return {
    ...Object.fromEntries(
      (Object.keys(BRAND_VARIABLES) as (keyof BrandColors)[]).flatMap((key) =>
        BRAND_VARIABLES[key].map((variable) => [variable, colors[key]])
      )
    ),
    ...(look
      ? {
          "--radius": `calc(${look.radius}px / 1.4)`,
          "--button-radius": `${look.buttonRadius}px`,
        }
      : {}),
    ...(look?.font
      ? { "--font-poppins": look.font, "--font-geist": look.font }
      : {}),
  }
}

/** Which theme's colors a candidate's page shows: the one its address asks for ("light" or
 * "dark"; "default" is the visitor's own), else the one its invite asked for, else the
 * visitor's own. */
export function pickTheme(
  asked: string | null,
  inviteTheme: Theme | null | undefined,
  own: Theme
): Theme {
  if (asked === "light" || asked === "dark") {
    return asked
  }

  return asked === "default" ? own : (inviteTheme ?? own)
}
