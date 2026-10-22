"use client"

import Link from "next/link"
import { useRouter } from "next/navigation"
import { useTranslations } from "next-intl"
import { useState } from "react"
import { toast } from "sonner"

import { PendingBadge } from "@/components/company/pending-badge"
import { InputAction } from "@/components/input-action"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog"
import { apiFetch, serviceRefusal } from "@/lib/api"
import { bdi } from "@/lib/bidi"
import type { Verification, VerificationStatus } from "@/types/company"

/** "Verify" beside an unverified company's name (the pending clock while it's reviewed): its website, sent for a superadmin's review
 * once an owner or admin signs in with a work email on that domain (right away when it's
 * theirs). It says where it stands: waiting for that email, or declined and why; saving the
 * website again asks for a new review. */
export function VerifyCompany({
  companyId,
  websiteDomain,
  status,
  declineReason,
}: {
  companyId: string
  websiteDomain: string | null
  status: VerificationStatus
  declineReason: string | null
}) {
  const t = useTranslations("verify")
  const router = useRouter()
  const [open, setOpen] = useState(false)
  const [website, setWebsite] = useState(websiteDomain ?? "")
  const [saving, setSaving] = useState(false)

  async function save(event: React.FormEvent) {
    event.preventDefault()
    setSaving(true)

    try {
      const result = await apiFetch<Verification>(
        `/companies/companies/${companyId}/website`,
        { method: "PUT", body: JSON.stringify({ website }) }
      )
      toast.success(
        result.verified_domain
          ? t.rich("done", { domain: result.verified_domain, ...bdi })
          : result.verification_status === "pending"
            ? t("submitted")
            : t.rich("pending", {
                domain: result.website_domain ?? website,
                ...bdi,
              })
      )
      setOpen(false)
      router.refresh()
    } catch (error) {
      // Not a website, or a free mail service: the API says which.
      toast.error(serviceRefusal(error, [422]) ?? t("failed"))
    } finally {
      setSaving(false)
    }
  }

  return (
    <Dialog open={open} onOpenChange={(next) => !saving && setOpen(next)}>
      {status === "pending" ? (
        <PendingBadge
          className="size-7"
          render={
            <DialogTrigger
              render={
                <button
                  type="button"
                  aria-label={t("pendingBadge")}
                  className="relative z-10 inline-flex shrink-0 cursor-pointer align-middle text-muted-foreground transition-opacity hover:opacity-70"
                />
              }
            />
          }
        />
      ) : (
        <DialogTrigger
          data-testid="verify-company"
          render={
            <button
              type="button"
              className="shrink-0 cursor-pointer text-sm text-primary transition-opacity hover:opacity-70"
            />
          }
        >
          {t("verify")}
        </DialogTrigger>
      )}
      <DialogContent showCloseButton={false} className="sm:max-w-lg">
        <DialogHeader>
          <DialogTitle>{t("title")}</DialogTitle>
          <DialogDescription>{t("text")}</DialogDescription>
        </DialogHeader>
        {status === "pending" && (
          <p className="text-sm text-muted-foreground">{t("submitted")}</p>
        )}
        {status === "waiting_email" && websiteDomain && (
          <p className="text-sm text-muted-foreground">
            {t.rich("waitingEmail", { domain: websiteDomain, ...bdi })}
          </p>
        )}
        {status === "declined" && (
          <div className="space-y-1 text-sm">
            <p className="text-destructive">
              {t.rich("declined", { reason: declineReason ?? "none", ...bdi })}
            </p>
            <p className="text-muted-foreground">
              {t.rich("tryAgain", {
                contact: (chunks) => (
                  <Link
                    href="/contact"
                    className="underline underline-offset-4"
                  >
                    {chunks}
                  </Link>
                ),
              })}
            </p>
          </div>
        )}
        <form onSubmit={save} className="flex">
          <InputAction
            required
            maxLength={253}
            placeholder="acme.com"
            aria-label={t("website")}
            value={website}
            onChange={(event) => setWebsite(event.target.value)}
            action={t("save")}
            disabled={saving || !website.trim()}
          />
        </form>
        <DialogFooter showCloseButton />
      </DialogContent>
    </Dialog>
  )
}
