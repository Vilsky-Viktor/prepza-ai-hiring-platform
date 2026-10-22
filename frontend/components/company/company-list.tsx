"use client"

import { MessagesSquareIcon, UserRoundIcon } from "lucide-react"
import Link from "next/link"
import { useTranslations } from "next-intl"

import { CompanyLogo } from "@/components/company/company-logo"
import { RemoveCompany } from "@/components/company/remove-company"
import { PendingBadge } from "@/components/company/pending-badge"
import { VerifiedBadge } from "@/components/company/verified-badge"
import { Badge } from "@/components/ui/badge"
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip"
import { VirtualList } from "@/components/virtual-list"
import { usePagedList } from "@/hooks/use-paged-list"
import { firstGrapheme } from "@/lib/graphemes"
import { byId } from "@/lib/paged-list"
import type { Company } from "@/types/company"
import { LIST_BOX } from "@/constants/lists"

const PATH = "/companies/companies"

/** The companies the user belongs to, a page at a time; `initial` is the server's first page.
 * With `templateId`, each row opens that template in the company instead (choosing where to use
 * a free test), without Remove. */
export function CompanyList({
  initial,
  templateId,
}: {
  initial: Company[]
  templateId?: string
}) {
  const t = useTranslations("company")
  const roles = useTranslations("roles")
  const { items, setItems, loadMore } = usePagedList(PATH, byId, initial)

  if (items.length === 0) {
    return (
      <p className="rounded-2xl border p-6 text-muted-foreground">
        {t("empty")}
      </p>
    )
  }

  return (
    <VirtualList
      items={items}
      getKey={byId}
      estimateSize={93}
      onEndReached={loadMore}
      className={`${LIST_BOX} overflow-hidden`}
      renderItem={(company) => (
        // One hover surface: the link stretches over the whole row, Remove sits on top of it.
        <div className="relative flex items-center gap-2 pe-3 transition-colors hover:bg-muted/50 active:bg-muted/50">
          <Link
            href={
              templateId
                ? `/companies/${company.id}/templates/${templateId}`
                : `/companies/${company.id}/interviews`
            }
            className="flex min-w-0 flex-1 items-center justify-between gap-4 py-8 after:absolute after:inset-0 max-sm:ps-6"
          >
            <span className="flex min-w-0 items-center gap-2">
              {/* The logo, or the first letter, as in the company's header: a square the
                  row's full height (32px padding twice, plus the name's line), from its
                  left border. Phones show only the name. */}
              <span className="-my-8 me-4 flex size-23 shrink-0 items-center justify-center overflow-hidden bg-muted max-sm:hidden">
                {company.logo_url ? (
                  <CompanyLogo
                    url={company.logo_url}
                    name={company.name}
                    className="size-full object-contain"
                  />
                ) : (
                  <span className="font-heading text-2xl font-medium text-muted-foreground uppercase">
                    {firstGrapheme(company.name)}
                  </span>
                )}
              </span>
              <span className="text-xl font-medium">{company.name}</span>
              {company.verified_domain && (
                <VerifiedBadge
                  domain={company.verified_domain}
                  className="size-5"
                />
              )}
              {company.verification_status === "pending" && (
                <PendingBadge className="size-5" />
              )}
              {company.role === "owner" && (
                <Tooltip>
                  <TooltipTrigger
                    render={
                      <span
                        role="img"
                        aria-label={t("owner")}
                        className="relative z-10 text-muted-foreground"
                      />
                    }
                  >
                    <UserRoundIcon className="size-5" />
                  </TooltipTrigger>
                  <TooltipContent>{t("owner")}</TooltipContent>
                </Tooltip>
              )}
            </span>
            <span className="flex shrink-0 items-center gap-4">
              <Tooltip>
                {/* Above the row's link overlay, so hovering it shows the tooltip. */}
                <TooltipTrigger
                  render={
                    <span
                      className="relative z-10 flex items-center gap-1.5 text-sm text-muted-foreground tabular-nums max-sm:hidden"
                      aria-label={t("interviewCount", {
                        count: company.interview_count,
                      })}
                    />
                  }
                >
                  <MessagesSquareIcon aria-hidden className="size-5" />
                  {company.interview_count}
                </TooltipTrigger>
                <TooltipContent>
                  {t("interviewCount", { count: company.interview_count })}
                </TooltipContent>
              </Tooltip>
              {company.role !== "owner" && (
                <Badge
                  variant="secondary"
                  className="h-7 px-3 text-sm font-light"
                >
                  {roles(company.role)}
                </Badge>
              )}
            </span>
          </Link>
          {company.can_delete && !templateId && (
            <div className="relative z-10 shrink-0">
              <RemoveCompany
                companyId={company.id}
                name={company.name}
                onRemoved={() =>
                  setItems((current) =>
                    current.filter((item) => item.id !== company.id)
                  )
                }
              />
            </div>
          )}
        </div>
      )}
    />
  )
}
