"use client"

import { cn } from "cn"
import { CheckIcon, PlusIcon } from "lucide-react"
import { useTranslations } from "next-intl"

import { Button } from "@/components/ui/button"
import {
  Dialog,
  DialogClose,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { FloatingInput } from "@/components/ui/floating-field"
import { MAX_COMPANY_NAME_LENGTH } from "@/config/limits"
import { NEW_COMPANY } from "@/config/start-test"
import type { Company } from "@/types/company"

/** The window over the start box that asks which company the interview is for: the user's
 * companies (the first chosen at first) and a new one, whose name is asked for; a first company
 * only asks its name, with the free candidates it gets. Open while `companies` isn't null;
 * Cancel closes it, the description kept as typed. */
export function StartCompanyDialog({
  companies,
  chosen,
  onChoose,
  name,
  onName,
  nameError,
  busy,
  freeCandidates,
  onStart,
  onClose,
}: {
  companies: Company[] | null
  chosen: string
  onChoose: (id: string) => void
  name: string
  onName: (name: string) => void
  // The server's reason the name can't be used (it's taken), shown under the field.
  nameError: string | null
  busy: boolean
  freeCandidates: number | null
  onStart: (event: React.FormEvent) => void
  onClose: () => void
}) {
  const t = useTranslations("start")
  const common = useTranslations("common")
  const list = companies ?? []
  const adding = chosen === NEW_COMPANY
  const options = [
    ...list.map((company) => ({ id: company.id, label: company.name })),
    { id: NEW_COMPANY, label: t("newCompany") },
  ]

  return (
    <Dialog
      open={companies !== null}
      onOpenChange={(open) => !open && !busy && onClose()}
    >
      <DialogContent showCloseButton={false} className="sm:max-w-lg">
        <DialogHeader>
          <DialogTitle>
            {list.length ? t("whichCompany") : t("firstCompany")}
          </DialogTitle>
        </DialogHeader>
        {/* Many companies scroll inside, so the window keeps to the screen; the scrollbar has
            its own room at the end, clear of the cards, which still line up with the title. */}
        <form
          id="start-company-form"
          onSubmit={onStart}
          className="-me-4 max-h-[50dvh] space-y-4 overflow-y-auto p-1 pe-5"
        >
          {list.length > 0 && (
            <div
              role="radiogroup"
              aria-label={t("whichCompany")}
              className="space-y-2"
            >
              {options.map((option) => (
                <button
                  key={option.id}
                  type="button"
                  role="radio"
                  aria-checked={chosen === option.id}
                  onClick={() => onChoose(option.id)}
                  className={cn(
                    "flex w-full items-center gap-3 rounded-xl border border-transparent bg-surface p-4 text-start text-base transition-colors",
                    chosen === option.id ? "border-ring" : "hover:border-ring"
                  )}
                >
                  {option.id === NEW_COMPANY ? (
                    <PlusIcon className="size-4 shrink-0 text-muted-foreground" />
                  ) : (
                    <CheckIcon
                      className={cn(
                        "size-4 shrink-0",
                        chosen === option.id ? "text-primary" : "invisible"
                      )}
                    />
                  )}
                  <span className="min-w-0 truncate">{option.label}</span>
                </button>
              ))}
            </div>
          )}
          {adding && (
            <div className="space-y-2">
              <FloatingInput
                label={t("companyName")}
                maxLength={MAX_COMPANY_NAME_LENGTH}
                required
                value={name}
                onChange={(event) => onName(event.target.value)}
                aria-invalid={nameError !== null}
                aria-describedby={
                  nameError ? "start-company-name-error" : undefined
                }
                autoFocus
              />
              {nameError && (
                <p
                  id="start-company-name-error"
                  role="alert"
                  className="text-sm text-destructive"
                >
                  {nameError}
                </p>
              )}
              {list.length === 0 && freeCandidates !== null && (
                <p className="text-sm text-muted-foreground">
                  {t("freeCandidates", { count: freeCandidates })}
                </p>
              )}
            </div>
          )}
        </form>
        <DialogFooter>
          <DialogClose
            render={
              <Button
                variant="outline"
                className="h-10 px-5 text-base"
                disabled={busy}
              />
            }
          >
            {common("cancel")}
          </DialogClose>
          <Button
            type="submit"
            form="start-company-form"
            className="h-10 px-5 text-base"
            disabled={busy || (adding && !name.trim())}
          >
            {busy ? t("starting") : t("continue")}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
