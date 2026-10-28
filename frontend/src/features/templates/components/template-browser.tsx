import { SearchIcon } from "lucide-react"
import { getLocale, getTranslations } from "next-intl/server"

import { InputAction } from "@/components/common/input-action"
import { SearchedList } from "@/components/common/searched-list"
import {
  ALL_LANGUAGES,
  TemplateFilterBar,
} from "@/features/templates/components/template-filters"
import { TemplateList } from "@/features/templates/components/template-list"
import { DEFAULT_LOCALE } from "@/config/i18n"
import { MAX_TITLE_LENGTH } from "@/config/limits"
import { PAGE_SIZE, PUBLIC_TEMPLATES_PATH } from "@/config/lists"
import { publicFetch, serverFetch } from "@/lib/server-api"
import {
  templateChoice,
  templateQuery,
} from "@/features/templates/utils/templates"
import type { PracticeStatus } from "@/types/round"
import type { TemplateFilters, TemplateSummary } from "@/types/superadmin"

export type TemplateSearchParams = {
  q?: string
  level?: string
  lang?: string | string[]
}

/** The templates searched and filtered like the old public library, on the page at `base` (the
 * address keeps the choices). `listPath` is the API list; rows open under `openBase` (by their
 * readable slug with `bySlug`, the public practice pages), and carry a "Use template" button for
 * `companyId`. Until a language is chosen, the list shows the visitor's interface language and
 * English (every language with `allLanguages`, the admin zone's). `statuses` marks the templates
 * the signed-in talent practiced. Null when the list can't be read. */
export async function TemplateBrowser({
  base,
  listPath,
  params,
  openBase,
  companyId,
  bySlug,
  allLanguages,
  statuses,
}: {
  base: string
  listPath: string
  params: TemplateSearchParams
  openBase: string
  companyId?: string
  bySlug?: boolean
  allLanguages?: boolean
  statuses?: PracticeStatus[]
}) {
  const t = await getTranslations("templates")
  // The filters are the same for everyone: kept a while.
  const filters = await publicFetch<TemplateFilters>(
    "/library/templates/filters"
  )

  if (!filters) {
    return null
  }

  const asked = [params.lang ?? []].flat()
  // Nothing chosen yet: the visitor's own language and English, unless every language is asked.
  const preferred =
    asked.length > 0 || allLanguages
      ? asked
      : [await getLocale(), DEFAULT_LOCALE]
  const choice = templateChoice(params, asked, preferred, filters)
  const query = templateQuery(choice)
  const path = `${listPath}?${query}`
  const narrowed = Boolean(choice.q || choice.level || choice.languages.length)
  // The first page renders on the server; the rest load as the user scrolls.
  // The public catalog is the same for everyone, so it's read without the visitor's token, and
  // fresh: a template published or removed shows at once. The others are the visitor's own.
  const firstPath = `${path}&limit=${PAGE_SIZE}`
  const first =
    listPath === PUBLIC_TEMPLATES_PATH
      ? await publicFetch<TemplateSummary[]>(firstPath, { fresh: true })
      : await serverFetch<TemplateSummary[]>(firstPath)

  if (!first) {
    return null
  }

  return (
    <SearchedList>
      <form action={base} className="flex">
        <InputAction
          maxLength={MAX_TITLE_LENGTH}
          name="q"
          defaultValue={choice.q}
          placeholder={t("search")}
          aria-label={t("search")}
          action={t("searchAction")}
          icon={<SearchIcon className="size-5" />}
          // The level and languages sit inside the field, before its button.
          addon={
            <TemplateFilterBar base={base} filters={filters} current={choice} />
          }
        />
        {/* A new search keeps the level and languages. */}
        {choice.level && (
          <input type="hidden" name="level" value={choice.level} />
        )}
        {choice.languages.length === 0 && (
          <input type="hidden" name="lang" value={ALL_LANGUAGES} />
        )}
        {choice.languages.map((language) => (
          <input key={language} type="hidden" name="lang" value={language} />
        ))}
      </form>

      <TemplateList
        path={path}
        initial={first}
        empty={narrowed ? t("noMatches") : t("empty")}
        openBase={openBase}
        companyId={companyId}
        bySlug={bySlug}
        statuses={statuses}
      />
    </SearchedList>
  )
}
