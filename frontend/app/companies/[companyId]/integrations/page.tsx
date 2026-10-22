import { cookies } from "next/headers"
import { redirect } from "next/navigation"
import { getTranslations } from "next-intl/server"

import { AiAppsRow } from "@/components/company/ai-apps-row"
import { ApiRow } from "@/components/company/api-row"
import { AtsConnectionRow } from "@/components/company/ats-connection"
import { SlackRow } from "@/components/company/slack-connection"
import { CompanyHeader } from "@/components/company/company-header"
import { SignInPrompt } from "@/components/sign-in-prompt"
import { ATS_PROVIDERS } from "@/constants/ats"
import { TOKEN_COOKIE } from "@/constants/auth"
import { optionalFetch, serverFetch } from "@/lib/server-api"
import { translatedTitle } from "@/lib/site"
import { companyHeaderProps } from "@/lib/company-header"
import type { ApiSettings } from "@/types/api-access"
import type { AtsIntegrations, Company } from "@/types/company"
import type { AiConnection } from "@/types/connections"
import type { SlackOverview } from "@/types/notifications"
import { LIST_BOX } from "@/constants/lists"

export const generateMetadata = () => translatedTitle("company", "integrations")

/** The company's integrations: Slack, its ATSs, the API and AI apps, a row each laid out like
 * the companies list, in four groups, messaging first; each opens its own page. Everyone in the company sees them; owners and admins change them. */
export default async function IntegrationsPage({
  params,
}: {
  params: Promise<{ companyId: string }>
}) {
  const { companyId } = await params
  const signedIn = (await cookies()).has(TOKEN_COOKIE)
  const t = await getTranslations("ats")
  const ai = await getTranslations("aiApps")
  // Asked together: the API refuses each on its own when the company isn't theirs.
  const [company, integrations, slack, api, connections] = signedIn
    ? await Promise.all([
        serverFetch<Company>(`/companies/companies/${companyId}`),
        optionalFetch<AtsIntegrations>(
          `/ats/connections?company_id=${companyId}`
        ),
        optionalFetch<SlackOverview>(
          `/notifications/slack?company_id=${companyId}`
        ),
        optionalFetch<ApiSettings>(`/v1/manage?company_id=${companyId}`),
        optionalFetch<AiConnection[]>("/assistant/connections"),
      ])
    : [null, null, null, null, null]

  if (!signedIn) {
    return (
      <main className="mx-auto max-w-5xl px-6 py-12">
        <SignInPrompt />
      </main>
    )
  }

  if (!company) {
    redirect("/companies")
  }

  return (
    <main className="mx-auto max-w-5xl space-y-8 px-6 py-12">
      <CompanyHeader
        {...companyHeaderProps(company)}
        companyId={companyId}
        current="integrations"
      />
      {slack && (
        <section className="space-y-6">
          <h2 className="font-heading text-2xl font-medium">
            {t("messagingGroup")}
          </h2>
          <ul className={`${LIST_BOX} overflow-hidden`}>
            <SlackRow
              companyId={companyId}
              slack={slack}
              canEdit={company.can_edit}
            />
          </ul>
        </section>
      )}
      <section className="space-y-6">
        {/* An acronym: its capitals stay, though titles are lowercase. */}
        <h2 className="font-heading text-2xl font-medium normal-case">
          {t("atsGroup")}
        </h2>
        {integrations?.available ? (
          <ul className={`${LIST_BOX} overflow-hidden`}>
            {ATS_PROVIDERS.map((provider) => (
              <AtsConnectionRow
                key={provider.id}
                companyId={companyId}
                companyName={company.name}
                provider={provider}
                connection={
                  integrations.connections.find(
                    (item) => item.provider === provider.id
                  ) ?? null
                }
                canEdit={company.can_edit}
              />
            ))}
          </ul>
        ) : (
          <p className="rounded-2xl border p-6 text-muted-foreground">
            {/* Not loaded (its service failed), or not offered yet. */}
            {integrations === null ? t("connectionsFailed") : t("unavailable")}
          </p>
        )}
      </section>
      {api && (
        <section className="space-y-6">
          <h2 className="font-heading text-2xl font-medium normal-case">
            {t("apiGroup")}
          </h2>
          <ul className={`${LIST_BOX} overflow-hidden`}>
            <ApiRow companyId={companyId} settings={api} />
          </ul>
        </section>
      )}
      <section className="space-y-6">
        {/* "AI" keeps its capitals, though titles are lowercase. */}
        <h2 className="font-heading text-2xl font-medium normal-case">
          {ai("group")}
        </h2>
        <ul className={`${LIST_BOX} overflow-hidden`}>
          <AiAppsRow companyId={companyId} connections={connections ?? []} />
        </ul>
      </section>
    </main>
  )
}
