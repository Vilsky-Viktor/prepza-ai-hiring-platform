"use client"

import { cn } from "cn"
import { useRouter } from "next/navigation"
import { useTranslations } from "next-intl"
import { useId, useState } from "react"
import { toast } from "sonner"

import { BrandPreview } from "@/components/company/brand-preview"
import { BrandStyleFields } from "@/components/company/brand-style-fields"
import { ColorField } from "@/components/company/color-field"
import { TabNav, TabPanel } from "@/components/tab-nav"
import { Button } from "@/components/ui/button"
import { BRAND_GROUPS } from "@/constants/brand"
import { LIST_BOX } from "@/constants/lists"
import { apiErrorMessage, apiFetch } from "@/lib/api"
import type {
  BrandColorSets,
  BrandStyle,
  PrepzaBrand,
  SavedBrandColors,
  Theme,
} from "@/types/company"

const THEMES: Theme[] = ["light", "dark"]

/** A company's colors on its candidates' pages, a set for each theme, by group, beside a
 * preview of those pages, then their font and corner rounding (the same in both themes). Save
 * keeps what's on screen: the theme's colors, the font and the rounding; it refuses colors whose
 * text would be hard to read (companies says which). Reset brings back what was last saved;
 * reset to prepza defaults, shown while anything saved isn't prepza's, goes back to prepza's
 * colors in both themes, font and rounding. */
export function BrandColorsForm({
  companyId,
  saved,
  current,
  style,
  prepza,
}: {
  companyId: string
  saved: SavedBrandColors | null
  // The colors the candidates' pages use now (the company's, or prepza's), and their font and
  // rounding.
  current: BrandColorSets
  style: BrandStyle
  prepza: PrepzaBrand
}) {
  const t = useTranslations("brand")
  const router = useRouter()
  const [theme, setTheme] = useState<Theme>("light")
  const panel = useId()
  const [colors, setColors] = useState<BrandColorSets>(current)
  const [look, setLook] = useState(style)
  // What was last saved, and which themes have colors of their own.
  const [last, setLast] = useState({ colors: current, look: style })
  const [own, setOwn] = useState({
    light: Boolean(saved?.light),
    dark: Boolean(saved?.dark),
  })
  const [saving, setSaving] = useState(false)
  const shown = colors[theme]
  const colorsChanged = !same(shown, last.colors[theme])
  const lookChanged = !same(look, last.look)
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
  // again at the bottom (`centered`), centered; on a phone, centered with room above and below.
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
          onClick={() => {
            setColors((sets) => ({ ...sets, [theme]: last.colors[theme] }))
            setLook(last.look)
          }}
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
            {t("colorsTitle")}
          </h2>
          <p className="text-muted-foreground">{t("colorsText")}</p>
        </div>
        {actions()}
      </div>
      <TabNav
        items={THEMES.map((id) => ({ id, label: t(`themes.${id}`) }))}
        current={theme}
        onSelect={(id) => setTheme(id as Theme)}
        panel={panel}
      />
      <TabPanel
        id={panel}
        current={theme}
        className="grid gap-8 lg:grid-cols-2 lg:items-start"
      >
        <div className="space-y-10">
          <ul className={LIST_BOX}>
            {BRAND_GROUPS.map((group) => (
              <li
                key={group.id}
                className="space-y-4 p-6"
                data-testid={`brand-${group.id}`}
              >
                <div className="space-y-1">
                  <span className="block text-xl font-medium">
                    {t(`groups.${group.id}.name`)}
                  </span>
                  <p className="text-sm text-muted-foreground">
                    {t(`groups.${group.id}.text`)}
                  </p>
                </div>
                <div className="flex flex-wrap gap-4">
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
                </div>
              </li>
            ))}
          </ul>
          <div className="space-y-4">
            <div className="space-y-1">
              <h3 className="text-xl font-medium">{t("styleTitle")}</h3>
              <p className="text-sm text-muted-foreground">{t("styleText")}</p>
            </div>
            <BrandStyleFields look={look} onChange={setLook} />
          </div>
        </div>
        <div className="space-y-3 lg:sticky lg:top-6">
          <p className="text-sm text-muted-foreground">{t("preview")}</p>
          <BrandPreview colors={shown} look={look} />
        </div>
      </TabPanel>
      {actions(true)}
    </section>
  )
}

/** Whether two flat objects hold the same values. */
function same<T extends object>(first: T, second: T) {
  return (Object.keys(first) as (keyof T)[]).every(
    (key) => first[key] === second[key]
  )
}
