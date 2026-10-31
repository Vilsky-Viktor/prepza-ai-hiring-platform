"use client"

import { PencilIcon, Trash2Icon } from "lucide-react"
import { useRouter } from "next/navigation"
import { useTranslations } from "next-intl"
import { useState } from "react"
import { toast } from "sonner"

import { ConfirmDialog } from "@/components/common/confirm-dialog"
import { IconButton } from "@/components/common/icon-button"
import { RenameCompanyDialog } from "@/features/superadmin/components/rename-company-dialog"
import { Button } from "@/components/ui/button"
import { apiErrorMessage, apiFetch } from "@/lib/api"
import { bdi, bdiText } from "@/lib/bidi"

type Step = "suspend" | "delete" | "rename"

/** What a superadmin can do about a company that impersonates another or abuses testee:
 * suspend it (or lift that), rename it, or delete it, each after a confirmation. The page is
 * read again after a change; a deleted company leads back to the search. */
export function CompanyActions({
  company,
}: {
  company: { id: string; name: string; suspended: boolean }
}) {
  const t = useTranslations("superadmin")
  const router = useRouter()
  const [asking, setAsking] = useState<Step>()
  const [busy, setBusy] = useState(false)
  const path = `/companies/superadmin/companies/${company.id}`

  async function act(
    method: string,
    url: string,
    done: string,
    after: () => void
  ) {
    setBusy(true)

    try {
      await apiFetch(url, { method })
      toast.success(done)
      setAsking(undefined)
      after()
    } catch (error) {
      toast.error(apiErrorMessage(error, t("actionFailed")))
    } finally {
      setBusy(false)
    }
  }

  // Its own pieces in the page's row: the text button beside "adjust credits", and on phones
  // the icon buttons on the next line.
  return (
    <>
      {company.suspended ? (
        <Button
          variant="outline"
          className="h-10 px-5 text-base max-sm:flex-1"
          disabled={busy}
          data-testid="unsuspend"
          onClick={() =>
            act("POST", `${path}/unsuspend`, t("unsuspended"), router.refresh)
          }
        >
          {t("unsuspend")}
        </Button>
      ) : (
        <Button
          variant="outline"
          className="h-10 px-5 text-base max-sm:flex-1"
          disabled={busy}
          data-testid="suspend"
          onClick={() => setAsking("suspend")}
        >
          {t("suspend")}
        </Button>
      )}
      <span className="flex items-center gap-2 max-sm:basis-full max-sm:justify-center">
        <IconButton
          label={t.markup("renameCompany", { name: company.name, ...bdiText })}
          onClick={() => setAsking("rename")}
          className="size-10"
        >
          <PencilIcon className="size-5" />
        </IconButton>
        <IconButton
          label={t.markup("deleteCompany", { name: company.name, ...bdiText })}
          onClick={() => setAsking("delete")}
          className="size-10 hover:text-destructive"
        >
          <Trash2Icon className="size-5" />
        </IconButton>
      </span>
      <ConfirmDialog
        open={asking === "suspend"}
        onOpenChange={(open) => !open && setAsking(undefined)}
        title={t.rich("suspendTitle", { name: company.name, ...bdi })}
        text={t("suspendText")}
        confirm={t("suspend")}
        busy={busy}
        onConfirm={() =>
          act("POST", `${path}/suspend`, t("suspendedDone"), router.refresh)
        }
      />
      <ConfirmDialog
        open={asking === "delete"}
        onOpenChange={(open) => !open && setAsking(undefined)}
        title={t.rich("deleteCompanyTitle", { name: company.name, ...bdi })}
        text={t("deleteCompanyText")}
        confirm={t("deleteCompanyConfirm")}
        busy={busy}
        onConfirm={() =>
          act("DELETE", path, t("companyDeleted"), () =>
            router.push("/superadmin/support")
          )
        }
      />
      <RenameCompanyDialog
        company={company}
        open={asking === "rename"}
        onOpenChange={(open) => !open && setAsking(undefined)}
        onRenamed={router.refresh}
      />
    </>
  )
}
