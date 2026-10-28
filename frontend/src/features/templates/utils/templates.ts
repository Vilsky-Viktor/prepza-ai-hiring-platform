import {
  ALL_LANGUAGES,
  type TemplateChoice,
} from "@/features/templates/components/template-filters"
import type { TemplateFilters } from "@/types/superadmin"

/** The search and filters the address asks for (`q`, `level` and the `lang`s it gave, `asked`),
 * keeping only what the API offers; anything else in the address is ignored. Until a language
 * is chosen, the `preferred` ones; "all" means every language. */
export function templateChoice(
  params: { q?: string; level?: string },
  asked: string[],
  preferred: string[],
  filters: TemplateFilters
): TemplateChoice {
  return {
    q: params.q?.trim() ?? "",
    level: filters.levels.find((level) => level === params.level) ?? null,
    languages: asked.includes(ALL_LANGUAGES)
      ? []
      : filters.languages.filter((code) => preferred.includes(code)),
  }
}

/** The API list's query for a choice: its search, level and each language. */
export function templateQuery(choice: TemplateChoice): URLSearchParams {
  const query = new URLSearchParams()

  if (choice.q) {
    query.set("q", choice.q)
  }

  if (choice.level) {
    query.set("level", choice.level)
  }

  choice.languages.forEach((language) => query.append("language", language))

  return query
}
