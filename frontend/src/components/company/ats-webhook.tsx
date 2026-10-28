"use client"

import { useTranslations } from "next-intl"
import { useEffect, useState } from "react"
import { toast } from "sonner"

import { Chips } from "@/components/company/ats-steps"
import { CopyValue } from "@/components/copy-field"
import { InputAction } from "@/components/input-action"
import { WEBHOOKS, type AtsProvider } from "@/constants/ats"
import { apiErrorMessage, apiFetch } from "@/lib/api"

type Webhook = { url: string; secret: string }

/** Setting up the web hook that tells us a candidate moved stage, for an ATS whose web hook the
 * company sets up itself: where, which event, the address to paste, and the secret key, copied
 * from us (Greenhouse) or pasted from the ATS, which makes it (Teamtailor). */
export function AtsWebhook({
  companyId,
  provider,
}: {
  companyId: string
  provider: AtsProvider & { id: keyof typeof WEBHOOKS }
}) {
  const t = useTranslations("ats")
  const setup = WEBHOOKS[provider.id]
  const path = `/ats/${provider.id}/webhook?company_id=${companyId}`
  const [webhook, setWebhook] = useState<Webhook>()

  useEffect(() => {
    apiFetch<Webhook>(path)
      .then(setWebhook)
      .catch((error) =>
        toast.error(
          apiErrorMessage(error, t("loadFailed", { ats: provider.name }))
        )
      )
  }, [path, provider.name, t])

  return (
    <section className="space-y-3">
      <div className="space-y-1">
        <h3 className="text-lg font-medium">{t("webhookTitle")}</h3>
        <p className="text-base text-muted-foreground">
          {t("webhookText", { ats: provider.name })}
        </p>
      </div>
      <ol className="list-decimal space-y-3 ps-5 text-base text-muted-foreground">
        {setup.note && <li>{t(setup.note)}</li>}
        <li className="space-y-1.5">
          <span className="block">{t("stepOpen", { ats: provider.name })}</span>
          <Chips items={[...setup.path]} path />
        </li>
        <li className="space-y-1.5">
          <span className="block">{t("webhookEvent")}</span>
          <Chips items={[setup.event]} />
        </li>
        <li className="space-y-2">
          <span className="block">{t("webhookUrl")}</span>
          <CopyValue
            value={webhook?.url ?? ""}
            label={t("copyUrl")}
            copied={t("copied")}
          />
        </li>
        <li className="space-y-2">
          {setup.pastesKey ? (
            <>
              <span className="block">
                {t(setup.pasteText ?? "webhookPasteKey", {
                  ats: provider.name,
                })}
              </span>
              {webhook && (
                <PastedKey
                  path={path}
                  saved={webhook.secret}
                  label={t(setup.keyName ?? "signatureKey")}
                />
              )}
            </>
          ) : (
            <>
              <span className="block">{t("webhookSecret")}</span>
              <CopyValue
                value={webhook?.secret ?? ""}
                label={t("copySecret")}
                copied={t("copied")}
              />
            </>
          )}
        </li>
      </ol>
    </section>
  )
}

/** The signature key the ATS made for the web hook, pasted and saved; shown once saved. */
function PastedKey({
  path,
  saved,
  label,
}: {
  path: string
  saved: string
  label: string
}) {
  const t = useTranslations("ats")
  const [key, setKey] = useState(saved)
  const [stored, setStored] = useState(saved)
  const [saving, setSaving] = useState(false)

  async function save(event: React.FormEvent) {
    event.preventDefault()
    setSaving(true)

    try {
      await apiFetch(path, {
        method: "PUT",
        body: JSON.stringify({ secret: key }),
      })
      setStored(key)
      toast.success(t("keySaved"))
    } catch (error) {
      toast.error(apiErrorMessage(error, t("keySaveFailed")))
    } finally {
      setSaving(false)
    }
  }

  return (
    <form onSubmit={save} className="flex">
      <InputAction
        required
        type="password"
        autoComplete="off"
        maxLength={500}
        placeholder={label}
        aria-label={label}
        value={key}
        onChange={(event) => setKey(event.target.value)}
        action={t("saveKey")}
        disabled={saving || !key || key === stored}
      />
    </form>
  )
}
