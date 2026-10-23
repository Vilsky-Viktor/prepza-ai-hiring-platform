"use client"

import { cn } from "cn"
import { useRouter } from "next/navigation"
import { useTranslations } from "next-intl"
import { useState } from "react"
import { toast } from "sonner"

import { BrandPreview } from "@/components/company/brand-preview"
import { BrandGroup } from "@/components/company/brand-group"
import {
  BrandFontField,
  BrandRoundingFields,
} from "@/components/company/brand-style-fields"
import { ColorField } from "@/components/company/color-field"
import { Button } from "@/components/ui/button"
import { BRAND_GROUPS } from "@/constants/brand"
import { FLOAT_LABEL, FLOAT_LABEL_UP } from "@/constants/floating-label"
import { LIST_BOX } from "@/constants/lists"
import { apiErrorMessage, apiFetch } from "@/lib/api"
import type {
  BrandColorSets,
  BrandStyle,
  PrepzaBrand,
  SavedBrandColors,
  Theme,
} from "@/types/company"

/** A company's colors on its candidates' pages, a set for each theme, by group, beside a
 * preview of those pages, then their font and corner rounding (the same in both themes). Save
 * keeps what's on screen: the theme's colors, the font and the rounding; it refuses colors whose
 * text would be hard to read (companies says which). Reset brings back what was last saved;
 * reset to prepza defaults, shown while anything saved isn't prepza's, goes back to prepza's
 * colors in both themes, font and rounding. Each part is a page of brand's in the side menu
 * (`page`): "general" holds the font and rounding (the logo is above it, on the page), each theme
 * its colors; save and reset act on what the page shows, and edits elsewhere are kept while
 * switching. */
export function BrandColorsForm({
  companyId,
  saved,
  current,
  style,
  prepza,
  page,
}: {
  companyId: string
  saved: SavedBrandColors | null
  // The colors the candidates' pages use now (the company's, or prepza's), and their font and
  // rounding.
  current: BrandColorSets
  style: BrandStyle
  prepza: PrepzaBrand
  page: "general" | Theme
}) {
  const t = useTranslations("brand")
  const router = useRouter()
  const [colors, setColors] = useState<BrandColorSets>(current)
  const [look, setLook] = useState(style)
  // What was last saved, and which themes have colors of their own.
  const [last, setLast] = useState({ colors: current, look: style })
  const [own, setOwn] = useState({
    light: Boolean(saved?.light),
    dark: Boolean(saved?.dark),
  })
  const [saving, setSaving] = useState(false)
  const general = page === "general"
  // General previews the light theme's colors.
  const theme = general ? "light" : page
  const shown = colors[theme]
  const colorsChanged = !general && !same(shown, last.colors[theme])
  const lookChanged = general && !same(look, last.look)
  const changed = colorsChanged || lookChanged
  const custom = own.light || own.dark || !same(last.look, prepza.style)

  async function put(path: string, body: unknown) {
    await apiFetch(`/companies/companies/${companyId}/${path}`, {
      method: "PUT",
      body: JSON.stringify(body),
    })
  }

  async function run(action: () => Promise<void>, done: string) {
    setSaving(true)

    try {
      await action()
      toast.success(done)
      router.refresh()
    } catch (error) {
      toast.error(apiErrorMessage(error, t("failed")))
    } finally {
      setSaving(false)
    }
  }

  const save = () =>
    run(async () => {
      if (colorsChanged) {
        await put(`brand-colors/${theme}`, { colors: shown })
        setOwn((themes) => ({ ...themes, [theme]: true }))
      }

      if (lookChanged) {
        await put("brand-style", look)
      }

      setLast((saved) => ({
        colors: { ...saved.colors, [theme]: shown },
        look,
      }))
    }, t("saved"))

  const resetToPrepza = () =>
    run(async () => {
      await put("brand-colors/light", { colors: null })
      await put("brand-colors/dark", { colors: null })
      await put("brand-style", prepza.style)
      setColors(prepza.colors)
      setLook(prepza.style)
      setLast({ colors: prepza.colors, look: prepza.style })
      setOwn({ light: false, dark: false })
    }, t("resetDone"))

  // Reset and save; under them, smaller, the way back to prepza's. At the top on the right and
  // again under the settings column (`centered`), centered; on a phone, centered with room above
  // and below.
  const actions = (centered = false) => (
    <div
      className={cn(
        "flex flex-col gap-2 max-sm:w-full max-sm:items-center max-sm:py-4",
        centered ? "w-full items-center" : "items-end"
      )}
    >
      <div className="flex gap-2">
        <Button
          variant="outline"
          className="h-12 px-6 text-base"
          disabled={saving || !changed}
          data-testid="brand-reset"
          onClick={() =>
            general
              ? setLook(last.look)
              : setColors((sets) => ({ ...sets, [theme]: last.colors[theme] }))
          }
        >
          {t("reset")}
        </Button>
        <Button
          className="h-12 px-6 text-base"
          disabled={saving || !changed}
          data-testid="brand-save"
          onClick={save}
        >
          {t("save")}
        </Button>
      </div>
      {custom && (
        <Button
          variant="ghost"
          size="sm"
          className="h-8 px-4 font-light"
          disabled={saving}
          data-testid="brand-reset-prepza"
          onClick={resetToPrepza}
        >
          {t("resetPrepza")}
        </Button>
      )}
    </div>
  )

  return (
    <section className="space-y-6">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div className="max-w-2xl space-y-2">
          <h2 className="font-heading text-2xl font-medium">
            {t(general ? "styleTitle" : "colorsTitle")}
          </h2>
          <p className="text-muted-foreground">
            {general ? t("styleText") : t("colorsText", { theme })}
          </p>
        </div>
        {actions()}
      </div>
      <div className="grid gap-8 lg:grid-cols-2 lg:items-start">
        <div className="space-y-8">
          {general ? (
            // The font and the rounding, each a group like the colors' (the same in both themes).
            <ul className={LIST_BOX} data-testid="brand-style">
              <BrandGroup
                id="font"
                name={t("groups.font.name")}
                text={t("groups.font.text")}
              >
                <BrandFontField look={look} onChange={setLook} />
              </BrandGroup>
              <BrandGroup
                id="rounding"
                name={t("groups.rounding.name")}
                text={t("groups.rounding.text")}
              >
                <BrandRoundingFields look={look} onChange={setLook} />
              </BrandGroup>
            </ul>
          ) : (
            <ul className={LIST_BOX}>
              {BRAND_GROUPS.map((group) => (
                <BrandGroup
                  key={group.id}
                  id={group.id}
                  name={t(`groups.${group.id}.name`)}
                  text={t(`groups.${group.id}.text`)}
                >
                  {group.colors.map((key) => (
                    <ColorField
                      key={`${theme}-${key}`}
                      label={t(`colors.${key}`)}
                      value={shown[key]}
                      onChange={(value) =>
                        setColors((sets) => ({
                          ...sets,
                          [theme]: { ...sets[theme], [key]: value },
                        }))
                      }
                    />
                  ))}
                </BrandGroup>
              ))}
            </ul>
          )}
          {actions(true)}
        </div>
        <div className="space-y-3 lg:sticky lg:top-6">
          {/* "Preview" on the preview's top border, as the landing's invite stage names its card. */}
          <div className="relative">
            <span
              className={cn(
                // The fields' raised label pill (its grey fill), centred, at this pill's size.
                FLOAT_LABEL,
                FLOAT_LABEL_UP,
                "start-1/2 z-10 -translate-x-1/2 px-4 py-1 text-sm lowercase rtl:translate-x-1/2"
              )}
            >
              {t("preview")}
            </span>
            <BrandPreview colors={shown} look={look} />
          </div>
        </div>
      </div>
    </section>
  )
}

/** Whether two flat objects hold the same values. */
function same<T extends object>(first: T, second: T) {
  return (Object.keys(first) as (keyof T)[]).every(
    (key) => first[key] === second[key]
  )
}
