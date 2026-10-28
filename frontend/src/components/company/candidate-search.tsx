import { SearchIcon } from "lucide-react"
import { getTranslations } from "next-intl/server"

import { CandidateSortMenu } from "@/components/company/candidate-sort"
import { CandidateStatusFilter } from "@/components/company/candidate-status-filter"
import { InputAction } from "@/components/input-action"
import type { CandidateSort } from "@/constants/interviews"
import { MAX_SEARCH_LENGTH } from "@/constants/limits"

/** Searches an interview's candidates by email, with the status and result filter and the sort inside the field, like
 * the templates search. A new search keeps the tab, sort and status. */
export async function CandidateSearch({
  action,
  sort,
  q,
  status,
  filters,
}: {
  action: string
  sort: CandidateSort
  q: string
  status: string | null
  filters: string[]
}) {
  const t = await getTranslations("candidates")

  return (
    <form action={action} className="flex">
      <InputAction
        maxLength={MAX_SEARCH_LENGTH}
        name="q"
        defaultValue={q}
        placeholder={t("search")}
        aria-label={t("search")}
        action={t("searchAction")}
        icon={<SearchIcon className="size-5" />}
        addon={
          <span className="flex shrink-0 items-center gap-1">
            <CandidateStatusFilter filters={filters} current={status} />
            <CandidateSortMenu current={sort} />
          </span>
        }
      />
      <input type="hidden" name="tab" value="candidates" />
      <input type="hidden" name="sort" value={sort} />
      {status && <input type="hidden" name="status" value={status} />}
    </form>
  )
}
