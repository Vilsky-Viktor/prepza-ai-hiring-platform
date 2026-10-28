import type { PageContext } from "@/types/assistant"
import type { PageHelpKey } from "@/types/page-help"

type RouteParams = Record<string, string | string[] | undefined>

/** The page a message is asked on, for the assistant: its guide's key, its path with the query
 * (the tab) and the ids its route names; null where no page registered a key (the admin
 * zone). */
export function pageContext(
  key: PageHelpKey | null,
  params: RouteParams,
  pathname: string
): PageContext | null {
  if (!key) {
    return null
  }

  const id = (name: string) => {
    const value = params[name]

    return typeof value === "string" ? value : undefined
  }

  return {
    key,
    path: pathname + window.location.search,
    company_id: id("companyId"),
    // `id` names an interview on a company's pages (/companies/<id>/interviews/<id>).
    interview_id: params.companyId ? id("id") : undefined,
    candidate_id: id("inviteId"),
    template_id: id("templateId"),
    practice_round_id: id("roundId"),
  }
}
