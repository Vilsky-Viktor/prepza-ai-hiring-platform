"use client"

import { useTranslations } from "next-intl"
import { useEffect, useRef } from "react"

import { CompanyCard } from "@/components/company/company-card"
import { usePagedList } from "@/hooks/use-paged-list"
import { byId } from "@/lib/paged-list"
import type { Company } from "@/types/company"
import { CARD } from "@/constants/cards"

const PATH = "/companies/companies"

/** The companies the user belongs to as a grid of cards, a page at a time; `initial` is the
 * server's first page. With `templateId`, each card opens that template in the company instead
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
  const end = useRef<HTMLDivElement>(null)

  // The next page loads as the grid's end nears the viewport; watched again after each page, so
  // an end still in view asks for one more.
  useEffect(() => {
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          loadMore()
        }
      },
      { rootMargin: "600px" }
    )

    if (end.current) {
      observer.observe(end.current)
    }

    return () => observer.disconnect()
  }, [items.length, loadMore])

  if (items.length === 0) {
    return <p className={`${CARD} text-muted-foreground`}>{t("empty")}</p>
  }

  return (
    <>
      <ul className="-mx-6 grid grid-cols-1 gap-6 sm:mx-0 sm:grid-cols-2 lg:grid-cols-3">
        {items.map((company) => (
          <li key={company.id}>
            <CompanyCard
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
          </li>
        ))}
      </ul>
      <div ref={end} />
    </>
  )
}
