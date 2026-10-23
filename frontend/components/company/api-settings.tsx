"use client"

import { useTranslations } from "next-intl"

import { useLocalTime } from "@/hooks/use-local-time"
import { CreateDialog, RemoveButton } from "@/components/company/api-dialogs"
import {
  EditPermissions,
  PermissionTags,
  PermissionTicks,
} from "@/components/company/api-permissions"
import { Dot } from "@/components/dot"
import { WebhookActions } from "@/components/company/webhook-actions"
import { MAX_KEY_NAME, MAX_WEBHOOK_URL } from "@/constants/api"
import type { ApiKey, ApiWebhook, PermissionOptions } from "@/types/api-access"
import { LIST_BOX } from "@/constants/lists"
import { bdi } from "@/lib/bidi"
import { hasMessage } from "@/lib/messages"
import { CARD } from "@/constants/cards"

/** "New key", in the title row while the keys tab is open: a name, when it expires and what it
 * may do (starting from the api service's defaults), then the key itself, shown this once. */
export function NewKey({
  companyId,
  expiries,
  options,
  defaults,
}: {
  companyId: string
  expiries: string[]
  options: PermissionOptions
  defaults: string[]
}) {
  const t = useTranslations("api")

  return (
    <CreateDialog
      path={`/v1/manage/keys?company_id=${companyId}`}
      field="name"
      maxLength={MAX_KEY_NAME}
      label={t("newKey")}
      placeholder={t("keyName")}
      title={t("newKeyTitle")}
      failed={t("createFailed")}
      choice={{
        field: "expiry",
        label: t("expiresIn"),
        options: expiries.map((expiry) => {
          const key = `expiries.${expiry}` as const

          return { value: expiry, label: hasMessage(t, key) ? t(key) : expiry }
        }),
        warning: { value: "never", text: t("neverWarning") },
      }}
      ticks={{
        field: "permissions",
        initial: defaults,
        render: (ticked, onChange) => (
          <PermissionTicks
            options={options}
            ticked={ticked}
            onChange={onChange}
          />
        ),
      }}
      shown={{
        value: "key",
        title: t("keyCreatedTitle"),
        text: t("keyCreatedText"),
        copy: t("copyKey"),
        copied: t("keyCopied"),
      }}
    />
  )
}

/** "Add web hook", in the title row while the web hooks tab is open: an HTTPS address, then its
 * signing secret, shown this once. */
export function AddWebhook({ companyId }: { companyId: string }) {
  const t = useTranslations("api")

  return (
    <CreateDialog
      path={`/v1/manage/webhooks?company_id=${companyId}`}
      field="url"
      type="url"
      maxLength={MAX_WEBHOOK_URL}
      label={t("addWebhook")}
      placeholder={t("webhookUrl")}
      title={t("addWebhookTitle")}
      failed={t("createFailed")}
      shown={{
        value: "secret",
        title: t("webhookCreatedTitle"),
        text: t("webhookCreatedText"),
        copy: t("copySecret"),
        copied: t("secretCopied"),
      }}
    />
  )
}

/** The company's API keys, in one list like the team's: each with its name, first characters,
 * when it was made, when it expires and when it was last used, and a line of its permissions.
 * Owners and admins narrow their permissions and delete them. */
export function ApiKeys({
  companyId,
  keys,
  options,
  canEdit,
}: {
  companyId: string
  keys: ApiKey[]
  options: PermissionOptions
  canEdit: boolean
}) {
  const t = useTranslations("api")
  const localTime = useLocalTime()
  const manage = `/v1/manage/keys`

  return (
    <Section
      text={t("keysText")}
      empty={t("noKeys")}
      rows={keys.map((key) => (
        <Row
          key={key.id}
          title={key.name}
          details={
            <>
              {t.rich("created", localTime.dateValues(key.created_at))}
              <Dot />
              {key.expired ? (
                <span className="text-destructive">{t("expired")}</span>
              ) : key.expires_at ? (
                t.rich("expires", localTime.dateValues(key.expires_at))
              ) : (
                t("neverExpires")
              )}
              <Dot />
              {key.last_used_at
                ? t.rich("lastUsed", localTime.dateValues(key.last_used_at))
                : t("neverUsed")}
            </>
          }
          more={
            <PermissionTags
              permissions={key.permissions}
              groups={options.permission_groups}
            />
          }
          remove={
            canEdit && (
              <span className="flex shrink-0 items-center">
                <EditPermissions
                  companyId={companyId}
                  apiKey={key}
                  options={options}
                />
                <RemoveButton
                  path={`${manage}/${key.id}?company_id=${companyId}`}
                  label={t("removeKey")}
                  title={t("removeKeyTitle")}
                  text={t.rich("removeKeyText", { name: key.name, ...bdi })}
                  failed={t("removeFailed")}
                />
              </span>
            )
          }
        />
      ))}
    />
  )
}

/** The addresses that hear the company's events; owners and admins send them a test event and
 * delete them, and anyone sees each one's delivery log. */
export function ApiWebhooks({
  companyId,
  webhooks,
  canEdit,
}: {
  companyId: string
  webhooks: ApiWebhook[]
  canEdit: boolean
}) {
  const t = useTranslations("api")
  const localTime = useLocalTime()
  const manage = `/v1/manage/webhooks`

  return (
    <Section
      text={t("webhooksText")}
      empty={t("noWebhooks")}
      rows={webhooks.map((hook) => (
        <Row
          key={hook.id}
          title={hook.url}
          details={
            <>
              {t.rich("added", localTime.dateValues(hook.created_at))}
              {(hook.stopped || hook.failing) && (
                <>
                  <Dot />
                  <span className="text-destructive">
                    {t(hook.stopped ? "stopped" : "failing")}
                  </span>
                </>
              )}
            </>
          }
          remove={
            <span className="flex shrink-0 items-center">
              <WebhookActions
                companyId={companyId}
                hook={hook}
                canEdit={canEdit}
              />
              {canEdit && (
                <RemoveButton
                  path={`${manage}/${hook.id}?company_id=${companyId}`}
                  label={t("removeWebhook")}
                  title={t("removeWebhookTitle")}
                  text={t.rich("removeWebhookText", { url: hook.url, ...bdi })}
                  failed={t("removeFailed")}
                />
              )}
            </span>
          }
        />
      ))}
    />
  )
}

/** What the tab is for, then its list, or a box saying it's empty. */
function Section({
  text,
  empty,
  rows,
}: {
  text: string
  empty: string
  rows: React.ReactNode[]
}) {
  return (
    <section className="space-y-6">
      <p className="text-base text-muted-foreground">{text}</p>
      {rows.length ? (
        <ul className={LIST_BOX}>{rows}</ul>
      ) : (
        <p className={`${CARD} text-muted-foreground`}>{empty}</p>
      )}
    </section>
  )
}

function Row({
  title,
  details,
  more,
  remove,
}: {
  title: string
  details: React.ReactNode
  // A column centred between the title and the actions, if any (a key's permissions); under the
  // title on phones.
  more?: React.ReactNode
  remove: React.ReactNode
}) {
  return (
    <li className="flex flex-wrap items-center gap-4 p-6 sm:flex-nowrap">
      <span
        className={`min-w-0 space-y-1 ${more ? "max-sm:flex-1" : "flex-1"}`}
      >
        <span className="block text-lg font-medium break-all">{title}</span>
        <span className="block text-sm text-muted-foreground">{details}</span>
      </span>
      {/* Centred in the room between the title and the actions. */}
      {more && (
        <span className="order-last w-full sm:order-none sm:flex sm:flex-1 sm:justify-center">
          {more}
        </span>
      )}
      {remove}
    </li>
  )
}
