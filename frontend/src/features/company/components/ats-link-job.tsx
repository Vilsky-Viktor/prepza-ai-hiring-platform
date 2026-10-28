"use client"

import { useRouter } from "next/navigation"
import { useTranslations } from "next-intl"
import { useState } from "react"
import { toast } from "sonner"

import { DescriptionBox } from "@/components/common/description-box"
import { InterviewPicker } from "@/features/company/components/interview-picker"
import { PillSelect } from "@/components/common/pill-select"
import { Button } from "@/components/ui/button"
import {
  Dialog,
  DialogClose,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog"
import type { Locale } from "@/config/i18n"
import type { AtsProvider } from "@/config/ats"
import { apiErrorMessage, apiFetch } from "@/lib/api"
import type { AtsItem, Interview } from "@/types/company"
import { CARD_PADDING } from "@/config/cards"

// The interview menu's first choice: a new interview made from the job's own text.
const NEW = "new"

/** "Link a job": an ATS's job, the stage that sends its candidates the interview, and which
 * interview. Jobs load when the dialog opens, a job's stages once it's chosen. "New interview
 * from this job" shows the job's text from the ATS to edit, then makes the interview from it,
 * links it, and opens its topic review, which goes on to the new interview, as from the home
 * page. */
export function LinkJob({
  companyId,
  provider,
  interviews,
}: {
  companyId: string
  provider: AtsProvider
  interviews: Interview[]
}) {
  const t = useTranslations("ats")
  const common = useTranslations("common")
  const start = useTranslations("start")
  const router = useRouter()
  const [open, setOpen] = useState(false)
  const [jobs, setJobs] = useState<AtsItem[] | null>(null)
  const [stages, setStages] = useState<AtsItem[] | null>(null)
  const [job, setJob] = useState<string | null>(null)
  const [stage, setStage] = useState<string | null>(null)
  const [interview, setInterview] = useState<string | null>(null)
  // The job's text for a new interview, once loaded.
  const [jobText, setJobText] = useState<string | null>(null)
  const [saving, setSaving] = useState(false)
  const base = `/ats/${provider.id}/jobs`

  async function openDialog(next: boolean) {
    if (saving) {
      return
    }

    setOpen(next)

    if (next && jobs === null) {
      try {
        setJobs(await apiFetch<AtsItem[]>(`${base}?company_id=${companyId}`))
      } catch (error) {
        toast.error(
          apiErrorMessage(error, t("loadFailed", { ats: provider.name }))
        )
        setOpen(false)
      }
    }
  }

  async function loadText(jobId: string) {
    setJobText(null)

    try {
      const found = await apiFetch<{ text: string }>(
        `${base}/${encodeURIComponent(jobId)}/text?company_id=${companyId}`
      )
      setJobText(found.text)
    } catch (error) {
      toast.error(
        apiErrorMessage(error, t("loadFailed", { ats: provider.name }))
      )
    }
  }

  async function chooseJob(id: string) {
    setJob(id)
    setStage(null)
    setStages(null)

    if (interview === NEW) {
      void loadText(id)
    }

    try {
      setStages(
        await apiFetch<AtsItem[]>(
          `${base}/${encodeURIComponent(id)}/stages?company_id=${companyId}`
        )
      )
    } catch (error) {
      toast.error(
        apiErrorMessage(error, t("loadFailed", { ats: provider.name }))
      )
    }
  }

  function chooseInterview(id: string) {
    setInterview(id)

    if (id === NEW && job) {
      void loadText(job)
    }
  }

  async function saveLink(interviewId: string) {
    await apiFetch(`/ats/links?company_id=${companyId}`, {
      method: "POST",
      body: JSON.stringify({
        provider: provider.id,
        job_id: job,
        stage_id: stage,
        interview_id: interviewId,
      }),
    })
  }

  async function link(event: React.FormEvent) {
    event.preventDefault()
    setSaving(true)

    try {
      await saveLink(interview as string)
      setOpen(false)
      setJob(null)
      setStage(null)
      setInterview(null)
      router.refresh()
    } catch (error) {
      toast.error(apiErrorMessage(error, t("linkFailed")))
    } finally {
      setSaving(false)
    }
  }

  // The new interview, as the home page makes one, linked at once; its topic review then goes
  // on to it.
  async function createAndLink(text: string, generateIn: Locale) {
    setSaving(true)

    try {
      const made = await apiFetch<Interview>(
        `/companies/interviews?company_id=${companyId}`,
        {
          method: "POST",
          body: JSON.stringify({ text, generate_in: generateIn }),
        }
      )
      await saveLink(made.id)
      router.push(
        `/generate/${made.generation_id}?next=/companies/${companyId}/interviews/${made.id}`
      )
    } catch (error) {
      toast.error(apiErrorMessage(error, t("linkFailed")))
      setSaving(false)
    }
  }

  const items = (list: AtsItem[] | null) =>
    (list ?? []).map((item) => ({
      value: item.id,
      label: item.name,
      keepCase: true,
    }))
  const fromJob = interview === NEW

  return (
    <Dialog open={open} onOpenChange={openDialog}>
      <DialogTrigger
        data-testid="link-job"
        render={<Button className="h-12 px-6 text-base" />}
      >
        {t("linkJob")}
      </DialogTrigger>
      <DialogContent showCloseButton={false} className="sm:max-w-2xl">
        <DialogHeader>
          <DialogTitle>{t("linkJob")}</DialogTitle>
        </DialogHeader>
        <form id="link-job" onSubmit={link} className="space-y-3">
          <PillSelect
            label={t("job")}
            placeholder={jobs === null ? t("loading") : t("pickJob")}
            value={job}
            options={items(jobs)}
            onChange={chooseJob}
            disabled={jobs === null || saving}
          />
          <PillSelect
            label={t("stage")}
            placeholder={t("pickStage")}
            value={stage}
            options={items(stages)}
            onChange={setStage}
            disabled={stages === null || saving}
          />
          <InterviewPicker
            companyId={companyId}
            interviews={interviews}
            first={{ value: NEW, label: t("newFromJob") }}
            label={t("interview")}
            value={interview}
            onChange={chooseInterview}
            disabled={saving}
          />
        </form>
        {/* The job's text from the ATS, to check and edit before the interview is made from
            it, in the home page's box. */}
        {fromJob && job && (
          <div className="space-y-2">
            <p className="text-sm text-muted-foreground">
              {t("jobTextNote", { ats: provider.name })}
            </p>
            {jobText === null ? (
              <p
                className={`rounded-xl bg-surface ${CARD_PADDING} text-muted-foreground`}
              >
                {t("loading")}
              </p>
            ) : (
              <DescriptionBox
                key={job}
                initialText={jobText}
                placeholder={start("placeholder")}
                label={t("jobText", { ats: provider.name })}
                submitLabel={t("createAndLink")}
                onSubmit={createAndLink}
                disabled={saving || !stage}
              />
            )}
          </div>
        )}
        <DialogFooter>
          <DialogClose
            render={
              <Button
                variant="outline"
                className="h-10 px-5 text-base"
                disabled={saving}
              />
            }
          >
            {common("cancel")}
          </DialogClose>
          {!fromJob && (
            <Button
              type="submit"
              form="link-job"
              className="h-10 px-5 text-base"
              disabled={saving || !job || !stage || !interview}
            >
              {t("linkJob")}
            </Button>
          )}
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
