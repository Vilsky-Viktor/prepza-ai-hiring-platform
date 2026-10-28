"use client"

import { UserRoundIcon, XIcon } from "lucide-react"
import Link from "next/link"
import { useRouter } from "next/navigation"
import { useTranslations } from "next-intl"
import { useState } from "react"
import { toast } from "sonner"

import { LinkJob } from "@/components/company/ats-link-job"
import { ConfirmDialog } from "@/components/confirm-dialog"
import { IconStat } from "@/components/icon-stat"
import { Button } from "@/components/ui/button"
import { apiErrorMessage, apiFetch } from "@/lib/api"
import { bdi } from "@/lib/bidi"
import type { AtsProvider } from "@/constants/ats"
import type { AtsJobLink, Interview } from "@/types/company"
import { LIST_BOX } from "@/constants/lists"
import { CARD } from "@/constants/cards"

/** The ATS's jobs linked to the company's interviews, on the ATS's own page, with "Link a job"
 * for owners and admins. */
export function AtsJobLinks({
  companyId,
  provider,
  links,
  interviews,
  canEdit,
}: {
  companyId: string
  provider: AtsProvider
  links: AtsJobLink[]
  interviews: Interview[]
  canEdit: boolean
}) {
  const t = useTranslations("ats")

  return (
    <section className="space-y-6">
      {/* On phones "Link a job" goes on its own line, full width. */}
      <div className="flex items-center justify-between gap-4 max-sm:flex-col max-sm:items-stretch max-sm:[&>button]:w-full">
        <div className="space-y-1">
          <h2 className="font-heading text-2xl font-medium">{t("links")}</h2>
          <p className="text-base text-muted-foreground">
            {t("linksText", { ats: provider.name })}
          </p>
        </div>
        {canEdit && (
          <LinkJob
            companyId={companyId}
            provider={provider}
            interviews={interviews}
          />
        )}
      </div>
      {links.length === 0 ? (
        <p className={`${CARD} text-muted-foreground`}>{t("noLinks")}</p>
      ) : (
        <ul className={LIST_BOX}>
          {links.map((link) => (
            <LinkRow
              key={link.id}
              companyId={companyId}
              link={link}
              canEdit={canEdit}
            />
          ))}
        </ul>
      )}
    </section>
  )
}

function LinkRow({
  companyId,
  link,
  canEdit,
}: {
  companyId: string
  link: AtsJobLink
  canEdit: boolean
}) {
  const t = useTranslations("ats")
  const router = useRouter()
  const [confirming, setConfirming] = useState(false)
  const [busy, setBusy] = useState(false)

  async function unlink() {
    setBusy(true)

    try {
      await apiFetch(`/ats/links/${link.id}?company_id=${companyId}`, {
        method: "DELETE",
      })
      setConfirming(false)
      router.refresh()
    } catch (error) {
      toast.error(apiErrorMessage(error, t("unlinkFailed")))
    } finally {
      setBusy(false)
    }
  }

  return (
    <li className="flex items-center justify-between gap-6 p-4 max-sm:flex-col max-sm:items-stretch max-sm:gap-4 sm:p-6">
      <span className="min-w-0 space-y-1">
        <span className="block text-lg font-medium">{link.job_name}</span>
        <span className="block text-base text-muted-foreground">
          {t.rich("linkLineTo", {
            stage: link.stage_name,
            interview: link.interview_title ?? t("generatingInterview"),
            ...bdi,
            link: (chunks) => (
              <Link
                href={`/companies/${companyId}/interviews/${link.interview_id}`}
                className="text-foreground underline-offset-4 hover:underline"
              >
                {chunks}
              </Link>
            ),
          })}
        </span>
        {link.waiting > 0 && (
          <span className="block text-sm text-muted-foreground">
            {t("waitingCount", { count: link.waiting })}
          </span>
        )}
      </span>
      {/* The stats, then Unlink, together at the row's end; on phones on a line of their own. */}
      <span className="flex shrink-0 items-center gap-4 max-sm:justify-between">
        <InvitedCount count={link.invited} />
        {link.not_invited > 0 && (
          <NotInvited companyId={companyId} link={link} canEdit={canEdit} />
        )}
        {canEdit && (
          <Button
            variant="ghost"
            size="icon"
            className="size-12 shrink-0 text-muted-foreground hover:text-destructive"
            aria-label={t("unlink")}
            onClick={() => setConfirming(true)}
          >
            <XIcon className="size-6" />
          </Button>
        )}
      </span>
      <ConfirmDialog
        open={confirming}
        onOpenChange={setConfirming}
        title={t("unlinkTitle")}
        text={t.rich("unlinkText", { job: link.job_name, ...bdi })}
        confirm={t("unlink")}
        busy={busy}
        onConfirm={unlink}
      />
    </li>
  )
}

/** Candidates invited from the ATS for this job: an icon and the number, in a column of its own
 * like a company's interview count, its meaning in a tooltip. */
function InvitedCount({ count }: { count: number }) {
  const t = useTranslations("ats")

  return (
    // me-4 and the negative start margin keep the count where it was: 1.5rem before the button.
    <IconStat
      label={t("invitedCount", { count })}
      icon={<UserRoundIcon aria-hidden className="size-5" />}
      className="me-4 text-sm"
      data-testid="invited-count"
    >
      {count}
    </IconStat>
  )
}

/** Candidates the ATS sent who weren't invited: their number in red, above "Invite again" for
 * owners and admins, which tries this job's again (after a top-up, or once the pause is off). */
function NotInvited({
  companyId,
  link,
  canEdit,
}: {
  companyId: string
  link: AtsJobLink
  canEdit: boolean
}) {
  const t = useTranslations("ats")
  const router = useRouter()
  const [busy, setBusy] = useState(false)

  async function retry() {
    setBusy(true)

    try {
      await apiFetch(`/ats/links/${link.id}/retry?company_id=${companyId}`, {
        method: "POST",
      })
      router.refresh()
    } catch (error) {
      toast.error(apiErrorMessage(error, t("inviteAgainFailed")))
    } finally {
      setBusy(false)
    }
  }

  return (
    <span
      className="flex flex-col items-center gap-2"
      data-testid="not-invited"
    >
      <span className="text-sm text-destructive">
        {t("notInvitedCount", { count: link.not_invited })}
      </span>
      {canEdit && (
        <Button
          variant="outline"
          className="h-10 px-5 text-base"
          disabled={busy}
          onClick={retry}
        >
          {t("inviteAgain")}
        </Button>
      )}
    </span>
  )
}
