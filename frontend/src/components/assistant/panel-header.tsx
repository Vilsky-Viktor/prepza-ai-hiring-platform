"use client"

import { HistoryIcon, SquarePenIcon, XIcon } from "lucide-react"
import { useTranslations } from "next-intl"

import { MenuPill } from "@/components/menu-pill"
import { Button } from "@/components/ui/button"
import { DialogClose } from "@/components/ui/dialog"
import type { Company } from "@/types/company"
import { ROUND_ICON_BUTTON } from "@/constants/buttons"

// The company picker's value for all companies.
const ALL = "all"

/** The assistant panel's header: the company picker (when there are `companies`; else
 * `title`), New chat, History (when `history` isn't null, pressed while it shows) and Close. */
export function PanelHeader({
  title,
  companies,
  company,
  onPick,
  history,
  onHistory,
  onNewChat,
}: {
  title: string
  companies: Company[]
  company: string | null
  onPick: (company: string | null) => void
  history: boolean | null
  onHistory: () => void
  onNewChat: () => void
}) {
  const t = useTranslations("assistant")
  const common = useTranslations("common")

  return (
    <div className="flex h-14 shrink-0 items-center gap-1 border-b px-4">
      <div className="min-w-0 flex-1" data-testid="assistant-company">
        {companies.length === 0 ? (
          <p className="truncate font-heading text-lg font-medium">{title}</p>
        ) : (
          <MenuPill
            ariaLabel={t("company")}
            value={company ?? ALL}
            options={[
              { value: ALL, label: t("allCompanies"), keepCase: true },
              ...companies.map((item) => ({
                value: item.id,
                label: item.name,
                keepCase: true,
              })),
            ]}
            onChange={(value) => onPick(value === ALL ? null : value)}
            className="h-9 max-w-60 px-4 pe-10 text-base [&>svg]:end-3 [&>svg]:size-5"
          />
        )}
      </div>
      <Button
        variant="ghost"
        size="icon"
        className={ROUND_ICON_BUTTON}
        aria-label={t("newChat")}
        data-testid="assistant-new-chat"
        onClick={onNewChat}
      >
        <SquarePenIcon className="size-5" />
      </Button>
      {history !== null && (
        <Button
          variant="ghost"
          size="icon"
          className={ROUND_ICON_BUTTON}
          aria-label={t("history")}
          data-testid="assistant-history"
          aria-pressed={history}
          onClick={onHistory}
        >
          <HistoryIcon className="size-5" />
        </Button>
      )}
      <DialogClose
        render={
          <Button
            variant="ghost"
            size="icon"
            className={ROUND_ICON_BUTTON}
            aria-label={common("close")}
            data-testid="assistant-close"
          />
        }
      >
        <XIcon className="size-5" />
      </DialogClose>
    </div>
  )
}
