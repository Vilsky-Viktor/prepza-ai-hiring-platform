"use client"

import { useTranslations } from "next-intl"
import { useState } from "react"
import { toast } from "sonner"

import { SettingsSection } from "@/components/common/settings-section"
import { Button } from "@/components/ui/button"
import { apiErrorMessage } from "@/lib/api"
import { setCompanyEmails } from "@/lib/superadmin-emails"
import type { CandidateOptOuts } from "@/types/superadmin"
import { LIST_BOX } from "@/config/lists"

type Company = CandidateOptOuts["companies"][number]

/** The companies that invited the address, or whose emails it stopped: each one's emails are
 * stopped here, or let through again when the person changed their mind. Only a stop made here
 * can be lifted here; the person's own, from an email's link, stay theirs. */
export function CompanyOptOuts({
  email,
  initial,
}: {
  email: string
  initial: CandidateOptOuts
}) {
  const t = useTranslations("superadmin")
  const [companies, setCompanies] = useState(initial.companies)
  const [saving, setSaving] = useState<string>()

  async function change(company: Company, stopped: boolean) {
    setSaving(company.company_id)

    try {
      const saved = await setCompanyEmails(email, company.company_id, stopped)
      setCompanies(saved.companies)
    } catch (error) {
      toast.error(apiErrorMessage(error, t("actionFailed")))
    } finally {
      setSaving(undefined)
    }
  }

  function state(company: Company) {
    if (company.stopped) {
      return t(
        company.stopped_by_admin ? "companyStopped" : "companyStoppedByThem"
      )
    }

    if (company.stopped_reminders > 0) {
      return t("remindersStopped", { count: company.stopped_reminders })
    }

    return t("companySending")
  }

  return (
    <SettingsSection
      title={t("companyEmails")}
      description={t("companyEmailsText")}
    >
      {companies.length === 0 ? (
        <p className="text-muted-foreground">{t("noCompanies")}</p>
      ) : (
        <div className={LIST_BOX}>
          {companies.map((company) => (
            <div
              key={company.company_id}
              className="flex items-center gap-6 p-4 sm:p-6"
            >
              <div className="min-w-0 flex-1 space-y-1">
                <p className="text-lg font-light break-words">{company.name}</p>
                <p className="text-sm text-muted-foreground">
                  {state(company)}
                </p>
              </div>
              {/* Stopping covers everything; letting through again lifts only a stop
                  made here. */}
              <span className="flex shrink-0 gap-2">
                {company.stopped_by_admin && (
                  <Button
                    variant="outline"
                    size="sm"
                    className="h-8 px-3 text-sm"
                    disabled={saving === company.company_id}
                    onClick={() => change(company, false)}
                    data-testid="resume-emails"
                  >
                    {t("resumeEmails")}
                  </Button>
                )}
                {!company.stopped && (
                  <Button
                    variant="outline"
                    size="sm"
                    className="h-8 px-3 text-sm"
                    disabled={saving === company.company_id}
                    onClick={() => change(company, true)}
                    data-testid="stop-emails"
                  >
                    {t("stopEmails")}
                  </Button>
                )}
              </span>
            </div>
          ))}
        </div>
      )}
    </SettingsSection>
  )
}
