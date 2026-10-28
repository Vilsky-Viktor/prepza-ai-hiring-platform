import { CodeXmlIcon } from "lucide-react"
import { cookies } from "next/headers"
import Link from "next/link"
import { redirect } from "next/navigation"
import { getTranslations } from "next-intl/server"

import { BackLink } from "@/components/common/back-link"
import { ApiNav } from "@/features/company/components/api-nav"
import {
  AddWebhook,
  ApiKeys,
  ApiWebhooks,
  NewKey,
} from "@/features/company/components/api-settings"
import { PageHeader } from "@/components/common/page-header"
import { SignInPrompt } from "@/components/common/sign-in-prompt"
import { Button } from "@/components/ui/button"
import { API_DOCS_PATH } from "@/config/api"
import { TOKEN_COOKIE } from "@/config/auth"
import { serverFetch } from "@/lib/server-api"
import type { ApiSettings } from "@/types/api-access"
import type { Company } from "@/types/company"

export const generateMetadata = async () => ({
  title: (await getTranslations("api"))("name"),
})

/** The API's own page, laid out like an interview's: back to the integrations tab, its name, the
 * docs and the open tab's action; then two tabs, the company's keys and its web hooks. */
export default async function ApiPage({
  params,
  searchParams,
}: {
  params: Promise<{ companyId: string }>
  searchParams: Promise<{ tab?: string }>
}) {
  const { companyId } = await params
  const current = (await searchParams).tab === "webhooks" ? "webhooks" : "keys"
  const href = `/companies/${companyId}/integrations/api`
  const signedIn = (await cookies()).has(TOKEN_COOKIE)
  const t = await getTranslations("company")
  const api = await getTranslations("api")
  // Asked together: the API refuses the settings on its own when the company isn't theirs.
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

  return (
    <main className="mx-auto max-w-page space-y-8 px-6 py-12">
      <div className="space-y-6">
        <PageHeader
          back={
            <BackLink href={`/companies/${companyId}/integrations`} help="api">
              {t("integrations")}
            </BackLink>
          }
          title={
            // On phones the buttons go on their own line, full width, sharing it equally.
            <div className="flex items-start justify-between gap-4 max-sm:flex-col max-sm:items-stretch">
              <div className="flex min-w-0 items-center gap-4">
                <span className="flex size-12 shrink-0 items-center justify-center rounded-xl bg-surface">
                  <CodeXmlIcon className="size-6" />
                </span>
                <div className="min-w-0 space-y-1">
                  <h1 className="font-heading text-3xl font-medium tracking-tight normal-case">
                    {api("name")}
                  </h1>
                </div>
              </div>
              {/* The docs, and the open tab's action for owners and admins. */}
              <div
                className="flex shrink-0 items-center gap-3 max-sm:mt-4 max-sm:*:flex-1"
                data-testid="integration-actions"
              >
                <Button
                  variant="outline"
                  className="h-10 px-5 text-base"
                  render={<Link href={API_DOCS_PATH} />}
                  nativeButton={false}
                >
                  {api("docs")}
                </Button>
                {company.can_edit &&
                  (current === "keys" ? (
                    <NewKey
                      companyId={companyId}
                      expiries={settings.expiries}
                      options={settings}
                      defaults={settings.default_permissions}
                    />
                  ) : (
                    <AddWebhook companyId={companyId} />
                  ))}
              </div>
            </div>
          }
        />
        <ApiNav href={href} current={current}>
          {current === "keys" ? (
            <ApiKeys
              companyId={companyId}
              keys={settings.keys}
              options={settings}
              canEdit={company.can_edit}
            />
          ) : (
            <ApiWebhooks
              companyId={companyId}
              webhooks={settings.webhooks}
              canEdit={company.can_edit}
            />
          )}
        </ApiNav>
      </div>
    </main>
  )
}
