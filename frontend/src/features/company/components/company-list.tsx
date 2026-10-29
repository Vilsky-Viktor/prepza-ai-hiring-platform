"use client"

import { useTranslations } from "next-intl"

import { CompanyRow } from "@/features/company/components/company-row"
import { VirtualList } from "@/components/common/virtual-list"
import { usePagedList } from "@/hooks/use-paged-list"
import { byId } from "@/lib/paged-list"
import type { Company } from "@/types/company"
import { LIST_BOX, LIST_EMPTY } from "@/config/lists"

const PATH = "/companies/companies"

/** The companies the user belongs to as a list of rows, a page at a time; `initial` is the
 * server's first page. With `templateId`, each row opens that template in the company instead
 * (choosing where to use a free test), without Remove. */
export function CompanyList({
  initial,
  templateId,
}: {
  initial: Company[]
  templateId?: string
}) {
  const t = useTranslations("company")
  const { items, setItems, loadMore } = usePagedList(PATH, byId, initial)

  if (items.length === 0) {
    return <p className={LIST_EMPTY}>{t("empty")}</p>
  }

  return (
    <VirtualList
      items={items}
      getKey={byId}
      estimateSize={101}
      onEndReached={loadMore}
      // Clips the first and last rows' logo tiles to the list's corners.
      className={`${LIST_BOX} overflow-hidden`}
      renderItem={(company) => (
        <CompanyRow
          company={company}
          href={
            templateId
              ? `/companies/${company.id}/templates/${templateId}`
              : `/companies/${company.id}/interviews`
          }
          removable={company.can_delete && !templateId}
          onRemoved={() =>
            setItems((current) =>
              current.filter((item) => item.id !== company.id)
            )
          }
        />
      )}
    />
  )
}
