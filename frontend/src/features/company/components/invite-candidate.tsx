"use client"

import { useRouter } from "next/navigation"
import { useTranslations } from "next-intl"
import { useId, useState } from "react"
import { toast } from "sonner"

import { InviteExample } from "@/features/company/components/invite-example"
import { InviteFileTab } from "@/features/company/components/invite-file-tab"
import { InviteProblems } from "@/features/company/components/invite-problems"
import { FloatingInput } from "@/components/ui/floating-field"
import { TabNav, TabPanel } from "@/components/common/tab-nav"
import { INVITE_TAB_ICONS } from "@/features/company/components/invite-tab-icons"
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
import { Textarea } from "@/components/ui/textarea"
import { INVITE_TAB_KEY, INVITE_TABS, type InviteTab } from "@/config/invites"
import {
  MAX_BULK_TEXT_LENGTH,
  MAX_CANDIDATE_NAME_LENGTH,
} from "@/config/limits"
import { ApiError, apiFetch } from "@/lib/api"
import { bdi } from "@/lib/bidi"
import type { BulkInviteResult } from "@/types/company"

/** "New candidate" beside the test's title: a dialog with three tabs, one email with an
 * optional name, a list, or a file. The API reads the emails and names and invites each; what
 * it couldn't stays in the tab with the reasons under it. The last tab used is remembered in
 * this browser. They take it in the interview's mode; a candidate's own mode is set on their
 * page. The candidate list (`candidatesHref`) shows the invited after. */
export function InviteCandidate({
  interviewId,
  candidatesHref,
  maxInvites,
}: {
  interviewId: string
  candidatesHref: string
  // The most candidates one list or file may invite; null when the API didn't say.
  maxInvites: number | null
}) {
  const t = useTranslations("interviews")
  const share = useTranslations("share")
  const common = useTranslations("common")
  const router = useRouter()
  const [open, setOpen] = useState(false)
  const [tab, setTab] = useState<InviteTab>("one")
  const panel = useId()
  const [email, setEmail] = useState("")
  const [name, setName] = useState("")
  const [text, setText] = useState("")
  const [file, setFile] = useState<File | null>(null)
  const [skipped, setSkipped] = useState<BulkInviteResult["skipped"]>([])
  const [problems, setProblems] = useState<BulkInviteResult["problems"]>([])
  const [error, setError] = useState("")
  const [sending, setSending] = useState(false)

  // The tab last used in this browser, as the dialog opens.
  function openDialog(next: boolean) {
    if (sending) {
      return
    }

    if (next) {
      setProblems([])

      try {
        const saved = localStorage.getItem(INVITE_TAB_KEY) as InviteTab

        setTab(INVITE_TABS.includes(saved) ? saved : "one")
      } catch {}
    }

    setOpen(next)
  }

  function choose(next: InviteTab) {
    setTab(next)
    setSkipped([])
    setProblems([])
    setError("")

    try {
      localStorage.setItem(INVITE_TAB_KEY, next)
    } catch {}
  }

  const ready = { one: email.trim(), many: text.trim(), file }[tab]

  async function send(event: React.FormEvent) {
    event.preventDefault()
    setSending(true)
    setError("")

    try {
      const list =
        tab === "one"
          ? { text: email, name }
          : tab === "many"
            ? { text }
            : { text: await file!.text(), filename: file!.name }
      const result = await apiFetch<BulkInviteResult>(
        `/companies/interviews/${interviewId}/candidates/bulk`,
        { method: "POST", body: JSON.stringify(list) }
      )

      if (result.invited.length > 0) {
        toast.success(
          result.invited.length === 1
            ? share.rich("sent", { email: result.invited[0], ...bdi })
            : t("invitedMany", { count: result.invited.length })
        )
        router.refresh()
      }

      setSkipped(result.skipped)
      setProblems(result.problems)

      // Only what wasn't invited from a list stays, to fix or send again: its unusable lines
      // and the emails that weren't invited.
      if (tab === "many") {
        setText(
          [
            ...result.problems.map((row) => row.line),
            ...result.skipped.map((row) => row.email),
          ].join("\n")
        )
      }

      if (result.skipped.length === 0 && result.problems.length === 0) {
        setEmail("")
        setName("")
        setFile(null)
        setOpen(false)
        router.push(candidatesHref)
      }
    } catch (failure) {
      // No emails, too many, or a name with several emails: the API says which.
      const invalid = failure instanceof ApiError && failure.status < 500
      setError(invalid ? failure.message : share("failed"))
    } finally {
      setSending(false)
    }
  }

  return (
    <Dialog open={open} onOpenChange={openDialog}>
      <DialogTrigger
        data-testid="new-candidate"
        render={
          <Button className="h-12 shrink-0 px-6 text-base max-sm:basis-full" />
        }
      >
        {t("newCandidate")}
      </DialogTrigger>
      <DialogContent showCloseButton={false} className="sm:max-w-lg">
        <DialogHeader>
          <DialogTitle>{t("newCandidate")}</DialogTitle>
        </DialogHeader>
        <TabNav
          items={INVITE_TABS.map((id) => ({
            id,
            label: t(`inviteTab.${id}`),
            icon: INVITE_TAB_ICONS[id],
          }))}
          current={tab}
          onSelect={(id) => choose(id as InviteTab)}
          panel={panel}
        />
        <TabPanel id={panel} current={tab}>
          <form
            id="invite-candidate-form"
            onSubmit={send}
            className="space-y-3"
          >
            {tab === "one" && (
              <>
                <FloatingInput
                  label={t("candidateEmail")}
                  type="email"
                  autoComplete="off"
                  placeholder="candidate@example.com"
                  value={email}
                  onChange={(event) => setEmail(event.target.value)}
                />
                <FloatingInput
                  label={t("candidateName")}
                  autoComplete="off"
                  maxLength={MAX_CANDIDATE_NAME_LENGTH}
                  value={name}
                  onChange={(event) => setName(event.target.value)}
                />
              </>
            )}
            {tab === "many" && (
              <>
                {/* A list: it grows as one is pasted. */}
                <Textarea
                  rows={3}
                  maxLength={MAX_BULK_TEXT_LENGTH}
                  placeholder="candidate@example.com"
                  aria-label={t("candidateEmails")}
                  value={text}
                  onChange={(event) => {
                    setText(event.target.value)
                    setSkipped([])
                  }}
                  className="max-h-64 min-h-28 resize-none rounded-xl border-transparent px-6 py-[18px] text-lg focus-visible:border-ring-gradient-field focus-visible:ring-0 md:text-lg"
                />
                <InviteExample maxInvites={maxInvites} />
              </>
            )}
            {tab === "file" && (
              <InviteFileTab
                maxInvites={maxInvites}
                file={file}
                onChoose={(chosen, tooLarge) => {
                  setFile(chosen)
                  setSkipped([])
                  setProblems([])
                  setError(tooLarge)
                }}
              />
            )}
            <InviteProblems
              error={error}
              problems={problems}
              skipped={skipped}
              center={tab === "file"}
            />
          </form>
        </TabPanel>
        <DialogFooter>
          <DialogClose
            render={
              <Button
                variant="outline"
                className="h-10 px-5 text-base"
                disabled={sending}
              />
            }
          >
            {common("cancel")}
          </DialogClose>
          <Button
            type="submit"
            form="invite-candidate-form"
            className="h-10 px-5 text-base"
            disabled={sending || !ready}
          >
            {t("invite")}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
