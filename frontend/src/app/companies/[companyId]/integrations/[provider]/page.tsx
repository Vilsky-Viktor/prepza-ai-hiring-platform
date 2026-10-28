import { cookies } from "next/headers"
import { notFound, redirect } from "next/navigation"
import { getTranslations } from "next-intl/server"

import { BackLink } from "@/components/common/back-link"
import {
  AtsAccount,
  AtsActions,
  AtsStatus,
} from "@/features/company/components/ats-connection"
import { AtsJobLinks } from "@/features/company/components/ats-job-links"
import { PageHeader } from "@/components/common/page-header"
import { SignInPrompt } from "@/components/common/sign-in-prompt"
import { ATS_PROVIDERS } from "@/config/ats"
import { TOKEN_COOKIE } from "@/config/auth"
import { serverFetch } from "@/lib/server-api"
import type {
  AtsIntegrations,
  AtsJobLink,
  Company,
  Interview,
} from "@/types/company"
import { CARD } from "@/config/cards"

type Params = Promise<{ companyId: string; provider: string }>

function providerOf(id: string) {
  return ATS_PROVIDERS.find((item) => item.id === id)
}

export const generateMetadata = async ({ params }: { params: Params }) => ({
  title: providerOf((await params).provider)?.name,
})

/** An ATS's own page, laid out like an interview's: back to the integrations tab, its status
 * and buttons, and once connected, its linked jobs with "Link a job" and Unlink; before, that it
 * isn't connected yet. */
export default async function AtsPage({ params }: { params: Params }) {
  const { companyId, provider: id } = await params
  const provider = providerOf(id)

  if (!provider) {
    notFound()
  }

  const signedIn = (await cookies()).has(TOKEN_COOKIE)
  const t = await getTranslations("company")
  const ats = await getTranslations("ats")
  // Asked together: the API refuses each on its own when the company isn't theirs.
  const [company, integrations, links, interviews] = signedIn
    ? await Promise.all([
        serverFetch<Company>(`/companies/companies/${companyId}`),
        serverFetch<AtsIntegrations>(
          `/ats/connections?company_id=${companyId}`
        ),
        serverFetch<AtsJobLink[]>(`/ats/links?company_id=${companyId}`),
        serverFetch<Interview[]>(
          `/companies/interviews?company_id=${companyId}&limit=100`
        ),
      ])
    : [null, null, null, null]

  if (!signedIn) {
    return (
      <main className="mx-auto max-w-page px-6 py-12">
        <SignInPrompt />
      </main>
    )
  }

  if (!company) {
    redirect("/companies")
  }

  if (!integrations?.available) {
    notFound()
  }

  const connection =
    integrations.connections.find((item) => item.provider === provider.id) ??
    null
  const connected = connection?.status === "connected"

  return (
    <main className="mx-auto max-w-page space-y-8 px-6 py-12">
      <PageHeader
        back={
          <BackLink href={`/companies/${companyId}/integrations`} help="ats">
            {t("integrations")}
          </BackLink>
        }
        title={
          // On phones the buttons go on their own line, full width, sharing it equally.
          <div className="flex items-start justify-between gap-4 max-sm:flex-col max-sm:items-stretch">
            <div className="flex min-w-0 items-center gap-4">
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img
                src={provider.logo}
                alt=""
                className="size-12 shrink-0 rounded-xl"
              />
              <div className="min-w-0 space-y-1">
                <div className="flex items-center gap-3">
                  <h1 className="font-heading text-3xl font-medium tracking-tight normal-case">
                    {provider.name}
                  </h1>
                  <span className="max-sm:hidden">
                    <AtsStatus connection={connection} />
                  </span>
                </div>
                <AtsAccount
                  connection={connection}
                  companyName={company.name}
                  className="block text-base text-muted-foreground"
                />
                {/* On phones its status goes under the name and account. */}
                <span className="mt-2 flex empty:hidden sm:hidden">
                  <AtsStatus connection={connection} />
                </span>
              </div>
            </div>
            <div className="max-sm:mt-4 max-sm:*:w-full max-sm:*:flex-wrap max-sm:[&>*>*]:flex-1 max-sm:[&>*>*:nth-child(3)]:basis-full">
              <AtsActions
                companyId={companyId}
                provider={provider}
                connection={connection}
                canEdit={company.can_edit}
              />
            </div>
          </div>
        }
      />
      {connection ? (
        <AtsJobLinks
          companyId={companyId}
          provider={provider}
          links={(links ?? []).filter((item) => item.provider === provider.id)}
          interviews={(interviews ?? []).filter((item) => item.set_id)}
          canEdit={company.can_edit && connected}
        />
      ) : (
        <p className={`${CARD} text-muted-foreground`}>
          {ats("notConnected", { ats: provider.name })}
        </p>
      )}
    </main>
  )
}
