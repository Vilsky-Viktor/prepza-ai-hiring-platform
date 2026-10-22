"use client"

import { cn } from "cn"
import { ArrowUpIcon, CheckIcon, PlusIcon } from "lucide-react"
import { useRouter } from "next/navigation"
import { useLocale, useTranslations } from "next-intl"
import { useState } from "react"
import { toast } from "sonner"

import { useSignIn } from "@/components/sign-in-dialog"
import { useAuth } from "@/components/auth-provider"
import { GenerateIn } from "@/components/generate-in"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import { useHumanCheck } from "@/hooks/use-human-check"
import type { Locale } from "@/constants/i18n"
import { MAX_COMPANY_NAME_LENGTH, MAX_GOAL_LENGTH } from "@/constants/limits"
import { COMPANIES_CHANGED } from "@/constants/notifications"
import { apiErrorMessage, apiFetch, serviceRefusal } from "@/lib/api"
import { refreshVerification } from "@/lib/auth"
import { humanHeaders } from "@/lib/human-check"
import { isSubmitShortcut } from "@/lib/keys"
import type { Company, Interview } from "@/types/company"

// The choice that adds a company instead of picking one.
const NEW = "new"

/** The home page's start: paste a job description, then, in the same box, sign in if needed and
 * say which company the test is for, and its generation begins. `freeCandidates` is how many
 * candidates a first company's welcome credits cover, from billing. */
export function StartTest({
  freeCandidates,
}: {
  freeCandidates: number | null
}) {
  const t = useTranslations("start")
  useHumanCheck()
  const common = useTranslations("common")
  const signIn = useSignIn()
  const router = useRouter()
  const { user } = useAuth()
  const [text, setText] = useState("")
  // Starts on the interface's language; any supported one can be chosen.
  const [generateIn, setGenerateIn] = useState(useLocale() as Locale)
  // Null while the description is being written; then the user's companies, maybe none.
  const [companies, setCompanies] = useState<Company[] | null>(null)
  const [chosen, setChosen] = useState<string>(NEW)
  const [name, setName] = useState("")
  // The server's reason the name can't be used (it's taken), shown under the field.
  const [nameError, setNameError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)

  async function describe(event: React.FormEvent) {
    event.preventDefault()
    setBusy(true)

    if (!user && !(await signIn())) {
      setBusy(false)

      return
    }

    try {
      // Only companies where the user may create a test: not those they only view.
      const found = (
        await apiFetch<Company[]>("/companies/companies?limit=100")
      ).filter((company) => company.can_edit)
      setCompanies(found)
      // The newest company is the likeliest; the list is oldest first.
      setChosen(found.at(-1)?.id ?? NEW)
    } catch (error) {
      toast.error(apiErrorMessage(error, t("failed")))
    }

    setBusy(false)
  }

  async function companyId() {
    if (chosen !== NEW) {
      return chosen
    }

    // A person's first company asks them to show they're a person (it gets the welcome credits),
    // and every company a verified email: one verified since signing in counts at once.
    await refreshVerification()
    const company = await apiFetch<Company>("/companies/companies", {
      method: "POST",
      body: JSON.stringify({ name: name.trim() }),
      headers: await humanHeaders(),
    })

    // The bell hears the new company at once.
    window.dispatchEvent(new Event(COMPANIES_CHANGED))
    // Picked from now on, so a failure after this doesn't create it twice.
    setCompanies((current) => [...(current ?? []), company])
    setChosen(company.id)

    return company.id
  }

  async function start(event: React.FormEvent) {
    event.preventDefault()
    setBusy(true)
    setNameError(null)

    try {
      const id = await companyId()
      const interview = await apiFetch<Interview>(
        `/companies/interviews?company_id=${id}`,
        {
          method: "POST",
          body: JSON.stringify({ text: text.trim(), generate_in: generateIn }),
        }
      )
      router.push(
        `/generate/${interview.generation_id}?next=/companies/${id}/interviews/${interview.id}`
      )
    } catch (error) {
      const refused = serviceRefusal(error, [409])

      if (refused) {
        setNameError(refused)
      } else {
        toast.error(apiErrorMessage(error, t("failed")))
      }

      setBusy(false)
    }
  }

  function handleKeyDown(event: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (isSubmitShortcut(event)) {
      event.preventDefault()
      event.currentTarget.form?.requestSubmit()
    }
  }

  // On phones the box spans the screen, with square corners.
  const box =
    "-mx-6 w-[calc(100%+3rem)] border border-transparent bg-muted p-3 transition-colors focus-within:border-ring sm:mx-0 sm:w-full sm:rounded-3xl dark:bg-card"

  if (companies === null) {
    return (
      <form onSubmit={describe} className={box}>
        <Textarea
          maxLength={MAX_GOAL_LENGTH}
          required
          value={text}
          onChange={(event) => setText(event.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={t("placeholder")}
          aria-label={t("description")}
          className="max-h-72 min-h-40 resize-none border-0 bg-transparent p-2 text-base shadow-none focus-visible:ring-0 max-[399px]:min-h-28 md:text-base dark:bg-transparent [@media(max-height:700px)]:min-h-28"
        />
        <div className="flex flex-wrap items-center justify-between gap-4 ps-2 pt-2">
          <p className="text-xs text-muted-foreground pointer-coarse:hidden">
            {common("submitHint")}
          </p>
          <div className="ms-auto flex items-center gap-3">
            <GenerateIn value={generateIn} onChange={setGenerateIn} />
            <Button
              type="submit"
              size="icon-lg"
              className="rounded-full"
              disabled={busy || !text.trim()}
              aria-label={t("submit")}
            >
              <ArrowUpIcon />
            </Button>
          </div>
        </div>
      </form>
    )
  }

  const adding = chosen === NEW

  return (
    <form onSubmit={start} className={cn(box, "space-y-4 p-6")}>
      <p className="font-heading text-xl font-medium">
        {companies.length ? t("whichCompany") : t("firstCompany")}
      </p>

      {companies.length > 0 && (
        <div
          role="radiogroup"
          aria-label={t("whichCompany")}
          className="space-y-2"
        >
          {[
            ...companies.map((c) => ({ id: c.id, label: c.name })),
            { id: NEW, label: t("newCompany") },
          ].map((option) => (
            <button
              key={option.id}
              type="button"
              role="radio"
              aria-checked={chosen === option.id}
              onClick={() => setChosen(option.id)}
              className={cn(
                "flex w-full items-center gap-3 rounded-2xl border bg-background p-4 text-start text-base transition-colors",
                chosen === option.id ? "border-ring" : "hover:border-ring"
              )}
            >
              {option.id === NEW ? (
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
          <Input
            maxLength={MAX_COMPANY_NAME_LENGTH}
            required
            value={name}
            onChange={(event) => {
              setName(event.target.value)
              setNameError(null)
            }}
            placeholder={t("companyName")}
            aria-label={t("companyName")}
            aria-invalid={nameError !== null}
            aria-describedby={
              nameError ? "start-company-name-error" : undefined
            }
            className="h-12 bg-background text-base"
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
          {companies.length === 0 && freeCandidates !== null && (
            <p className="text-sm text-muted-foreground">
              {t("freeCandidates", { count: freeCandidates })}
            </p>
          )}
        </div>
      )}

      <div className="flex flex-wrap items-center justify-between gap-3 pt-2">
        <Button
          type="button"
          variant="ghost"
          className="h-11 px-4 text-base"
          disabled={busy}
          onClick={() => setCompanies(null)}
        >
          {t("back")}
        </Button>
        <Button
          type="submit"
          className="h-11 px-6 text-base"
          disabled={busy || (adding && !name.trim())}
        >
          {busy ? t("starting") : t("continue")}
        </Button>
      </div>
    </form>
  )
}
