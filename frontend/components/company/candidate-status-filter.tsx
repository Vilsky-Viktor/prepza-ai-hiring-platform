"use client"

import { ChevronDownIcon } from "lucide-react"
import { usePathname, useRouter, useSearchParams } from "next/navigation"
import { useTranslations } from "next-intl"

import { Button } from "@/components/ui/button"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuRadioGroup,
  DropdownMenuRadioItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { hasMessage } from "@/lib/messages"

// "Any status" in the menu; the statuses and results themselves come from the API.
const ANY = "any"

/** The candidates' status, inside the search field; the choice lives in the address, so the
 * server renders the first page filtered. */
export function CandidateStatusFilter({
  filters,
  current,
}: {
  filters: string[]
  current: string | null
}) {
  const t = useTranslations("candidates")
  const labels = useTranslations("candidateStatus")
  const router = useRouter()
  const pathname = usePathname()
  const searchParams = useSearchParams()

  // A status from the API or the address, or as it is when there's no name for it.
  function named(status: string) {
    return hasMessage(labels, status) ? labels(status) : status
  }

  function choose(status: string) {
    const params = new URLSearchParams(searchParams)

    if (status === ANY) {
      params.delete("status")
    } else {
      params.set("status", status)
    }

    router.replace(`${pathname}?${params}`, { scroll: false })
  }

  return (
    <DropdownMenu>
      <DropdownMenuTrigger
        render={
          <Button
            type="button"
            variant="ghost"
            className="h-10 shrink-0 gap-1.5 px-3 text-sm"
          />
        }
      >
        {t("status", {
          status: current ? named(current) : t("anyStatus"),
        })}
        <ChevronDownIcon className="text-muted-foreground" />
      </DropdownMenuTrigger>
      <DropdownMenuContent align="start" className="w-48 p-2">
        <DropdownMenuRadioGroup value={current ?? ANY} onValueChange={choose}>
          <DropdownMenuRadioItem value={ANY} className="px-3 py-2 lowercase">
            {t("anyStatus")}
          </DropdownMenuRadioItem>
          {filters.map((status) => (
            <DropdownMenuRadioItem
              key={status}
              value={status}
              className="px-3 py-2 lowercase"
            >
              {named(status)}
            </DropdownMenuRadioItem>
          ))}
        </DropdownMenuRadioGroup>
      </DropdownMenuContent>
    </DropdownMenu>
  )
}
