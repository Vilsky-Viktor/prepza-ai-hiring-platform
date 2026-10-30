"use client"

import { ArrowUpIcon } from "lucide-react"
import { useRouter } from "next/navigation"
import { useLocale, useTranslations } from "next-intl"
import { useState } from "react"
import { toast } from "sonner"

import { StartCompanyDialog } from "@/components/common/start-company-dialog"
import { SubmitHint } from "@/components/common/submit-hint"
import { useSignIn } from "@/components/common/sign-in-dialog"
import { useAuth } from "@/providers/auth-provider"
import { GenerateIn } from "@/components/common/generate-in"
import { Button } from "@/components/ui/button"
import { Textarea } from "@/components/ui/textarea"
import { useHumanCheck } from "@/hooks/use-human-check"
import type { Locale } from "@/config/i18n"
import { MAX_GOAL_LENGTH } from "@/config/limits"
import { NEW_COMPANY } from "@/config/start-test"
import { COMPANIES_CHANGED } from "@/config/notifications"
import { apiErrorMessage, apiFetch, serviceRefusal } from "@/lib/api"
import { refreshVerification } from "@/lib/auth"
import { humanHeaders } from "@/lib/human-check"
import { isSubmitShortcut } from "@/lib/keys"
import type { Company, Interview } from "@/types/company"

/** The home page's start: paste a job description, then sign in if needed and, in a window over
 * the box, say which company the test is for, and its generation begins. `freeCandidates` is
 * how many candidates a first company's welcome credits cover, from billing. */
export function StartTest({
  freeCandidates,
}: {
  freeCandidates: number | null
}) {
  const t = useTranslations("start")
  useHumanCheck()
  const signIn = useSignIn()
  const router = useRouter()
  const { user } = useAuth()
  const [text, setText] = useState("")
  // Starts on the interface's language; any supported one can be chosen.
  const [generateIn, setGenerateIn] = useState(useLocale() as Locale)
  // Null while the description is being written; then the user's companies, maybe none.
  const [companies, setCompanies] = useState<Company[] | null>(null)
  const [chosen, setChosen] = useState<string>(NEW_COMPANY)
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
      // The first company in the list is chosen to start with.
      setChosen(found[0]?.id ?? NEW_COMPANY)
    } catch (error) {
      toast.error(apiErrorMessage(error, t("failed")))
    }

    setBusy(false)
  }

  async function companyId() {
    if (chosen !== NEW_COMPANY) {
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
    "relative -mx-6 w-[calc(100%+3rem)] border border-transparent bg-surface p-3 transition-colors focus-within:border-ring-gradient sm:mx-0 sm:w-full sm:rounded-xl"

  return (
    <>
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
          <SubmitHint />
          <div className="ms-auto flex items-center gap-3">
            <GenerateIn value={generateIn} onChange={setGenerateIn} />
            <Button
              type="submit"
              size="icon-lg"
              className="rounded-lg"
              disabled={busy || !text.trim()}
              aria-label={t("submit")}
            >
              <ArrowUpIcon />
            </Button>
          </div>
        </div>
      </form>
      <StartCompanyDialog
        companies={companies}
        chosen={chosen}
        onChoose={setChosen}
        name={name}
        onName={(next) => {
          setName(next)
          setNameError(null)
        }}
        nameError={nameError}
        busy={busy}
        freeCandidates={freeCandidates}
        onStart={start}
        onClose={() => setCompanies(null)}
      />
    </>
  )
}
