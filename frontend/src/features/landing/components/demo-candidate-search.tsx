"use client"

import { ChevronDownIcon, SearchIcon } from "lucide-react"
import { useTranslations } from "next-intl"

import { InputAction } from "@/components/common/input-action"
import { buttonVariants } from "@/components/ui/button"

// The candidates are listed best first.
const SORT = "grade"
const TRIGGER = buttonVariants({
  variant: "ghost",
  className: "h-10 shrink-0 gap-1.5 px-3 text-sm",
})

/** The candidates tab's search (features/company/components/candidate-search.tsx), for the
 * landing: the real field, empty, with the status filter and the sort inside it as their menus'
 * buttons show them, and the search button. */
export function DemoCandidateSearch() {
  const t = useTranslations("candidates")

  return (
    // In the picture the field keeps to its frame on phones too.
    <div className="flex max-sm:*:mx-0 max-sm:*:rounded-xl">
      <InputAction
        readOnly
        placeholder={t("search")}
        action={t("searchAction")}
        icon={<SearchIcon className="size-5" />}
        addon={
          <span className="flex shrink-0 items-center gap-1">
            <span className={TRIGGER}>
              {t("status", { status: t("anyStatus") })}
              <ChevronDownIcon className="text-muted-foreground" />
            </span>
            <span className={TRIGGER}>
              {t("sortBy", { sort: t(`sort.${SORT}`) })}
              <ChevronDownIcon className="text-muted-foreground" />
            </span>
          </span>
        }
      />
    </div>
  )
}
