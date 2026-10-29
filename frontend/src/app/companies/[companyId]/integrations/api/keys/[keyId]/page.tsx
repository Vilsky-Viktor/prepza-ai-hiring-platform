import { KeyRoundIcon } from "lucide-react"
import { cookies } from "next/headers"
import { redirect } from "next/navigation"
import { getTranslations } from "next-intl/server"

import { BackLink } from "@/components/common/back-link"
import { PageHeader } from "@/components/common/page-header"
import { SignInPrompt } from "@/components/common/sign-in-prompt"
import { RemoveButton } from "@/features/company/components/api-dialogs"
import { KeyIps } from "@/features/company/components/key-ips"
import {
  KeyPermissions,
  PermissionTags,
} from "@/features/company/components/api-permissions"
import { KeyDetails } from "@/features/company/components/key-details"
import { TOKEN_COOKIE } from "@/config/auth"
import { bdi } from "@/lib/bidi"
import { serverFetch } from "@/lib/server-api"
import type { ApiSettings } from "@/types/api-access"
import type { Company } from "@/types/company"

export const generateMetadata = async () => ({
  title: (await getTranslations("api"))("keysTitle"),
})

/** An API key's own page, laid out like an integration's: back to the API page, its name and
 * dates, and Delete for owners and admins; then its permissions and its allowed IPs. */
export default async function ApiKeyPage({
  params,
}: {
  params: Promise<{ companyId: string; keyId: string }>
}) {
  const { companyId, keyId } = await params
  const apiHref = `/companies/${companyId}/integrations/api`
  const signedIn = (await cookies()).has(TOKEN_COOKIE)
  const api = await getTranslations("api")
  const [company, settings] = signedIn
    ? await Promise.all([
        serverFetch<Company>(`/companies/companies/${companyId}`),
        serverFetch<ApiSettings>(`/v1/manage?company_id=${companyId}`),
      ])
    : [null, null]

  if (!signedIn) {
    return (
      <main className="mx-auto max-w-page px-6 py-12">
        <SignInPrompt />
      </main>
    )
  }

  if (!company || !settings) {
    redirect("/companies")
  }

  // A key that's gone (deleted here or elsewhere) leads back to the list.
  const apiKey = settings.keys.find((key) => key.id === keyId)

  if (!apiKey) {
    redirect(apiHref)
  }

  return (
    <main className="mx-auto max-w-page space-y-8 px-6 py-12">
      <PageHeader
        back={
          <BackLink href={apiHref} help="api">
            {api("name")}
          </BackLink>
        }
        title={
          <div className="flex items-start justify-between gap-4">
            <div className="flex min-w-0 items-center gap-4">
              <span className="flex size-12 shrink-0 items-center justify-center rounded-xl bg-surface">
                <KeyRoundIcon className="size-6" />
              </span>
              <div className="min-w-0 space-y-1">
                <h1 className="font-heading text-3xl font-medium tracking-tight break-all normal-case">
                  {apiKey.name}
                </h1>
                <p className="text-base text-muted-foreground">
                  <KeyDetails apiKey={apiKey} />
                </p>
              </div>
            </div>
            {company.can_edit && (
              <RemoveButton
                path={`/v1/manage/keys/${apiKey.id}?company_id=${companyId}`}
                label={api("removeKey")}
                title={api("removeKeyTitle")}
                text={api.rich("removeKeyText", { name: apiKey.name, ...bdi })}
                failed={api("removeFailed")}
              />
            )}
          </div>
        }
      />
      {/* Its permissions, and its allowed IPs beside them; stacked on smaller screens. */}
      <div className="grid gap-8 lg:grid-cols-2 lg:items-start">
        <section className="space-y-4">
          <h2 className="font-heading text-2xl font-medium">
            {api("permissionsTitle")}
          </h2>
          <p className="text-base text-muted-foreground">
            {api("permissionsText")}
          </p>
          {company.can_edit ? (
            <KeyPermissions
              companyId={companyId}
              apiKey={apiKey}
              options={settings}
            />
          ) : (
            <PermissionTags
              permissions={apiKey.permissions}
              groups={settings.permission_groups}
            />
          )}
        </section>
        <section className="space-y-4">
          <h2 className="font-heading text-2xl font-medium">
            {api("allowedIps")}
          </h2>
          <p className="text-base text-muted-foreground">
            {api("allowedIpsText")}
          </p>
          <KeyIps
            companyId={companyId}
            apiKey={apiKey}
            canEdit={company.can_edit}
          />
        </section>
      </div>
    </main>
  )
}
