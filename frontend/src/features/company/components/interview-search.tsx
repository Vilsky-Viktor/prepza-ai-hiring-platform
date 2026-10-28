import { SearchIcon } from "lucide-react"
import { getTranslations } from "next-intl/server"

import { InputAction } from "@/components/common/input-action"
import { MAX_SEARCH_LENGTH } from "@/config/limits"

/** Searches a company's interviews by title, like the templates and candidates searches; the
 * address keeps the search (`?q=`). */
export async function InterviewSearch({
  action,
  q,
}: {
  action: string
  q: string
}) {
  const t = await getTranslations("interviews")

  return (
    <form action={action} className="flex">
      <InputAction
        maxLength={MAX_SEARCH_LENGTH}
        name="q"
        defaultValue={q}
        dir="auto"
        placeholder={t("search")}
        aria-label={t("search")}
        action={t("searchAction")}
        icon={<SearchIcon className="size-5" />}
      />
    </form>
  )
}
