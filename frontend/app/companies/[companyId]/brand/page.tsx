import { cookies } from "next/headers"
import { redirect } from "next/navigation"
import { getTranslations } from "next-intl/server"

import { BrandColorsForm } from "@/components/company/brand-colors-form"
import { CompanyHeader } from "@/components/company/company-header"
import { LogoPicker } from "@/components/company/logo-picker"
import { SignInPrompt } from "@/components/sign-in-prompt"
import { TOKEN_COOKIE } from "@/constants/auth"
import { serverFetch } from "@/lib/server-api"
import { translatedTitle } from "@/lib/site"
import { companyHeaderProps } from "@/lib/company-header"
import type { Company, PrepzaBrand } from "@/types/company"

export const generateMetadata = () => translatedTitle("company", "brand")

/** How the company's candidates see its interviews: its logo, and its colors on their
 * invitation, questions and finished page. Owners and admins only, like billing. */
export default async function BrandPage({
  params,
}: {
  params: Promise<{ companyId: string }>
}) {
  const { companyId } = await params
  const t = await getTranslations("brand")
  const signedIn = (await cookies()).has(TOKEN_COOKIE)

  if (!signedIn) {
    return (
      <main className="mx-auto max-w-5xl px-6 py-12">
        <SignInPrompt />
      </main>
    )
  }

  const [company, prepza] = await Promise.all([
    serverFetch<Company>(`/companies/companies/${companyId}`),
    serverFetch<PrepzaBrand>("/companies/brand/prepza"),
  ])

  if (!company?.candidate_colors || !prepza) {
    redirect("/companies")
  }

  if (!company.can_edit) {
    redirect(`/companies/${companyId}/interviews`)
  }

  return (
    <main className="mx-auto max-w-5xl space-y-12 px-6 py-12">
      <CompanyHeader
        {...companyHeaderProps(company)}
        companyId={companyId}
        current="brand"

        className="space-y-12"
      >
        <section className="flex items-center gap-5">
          <LogoPicker
            companyId={companyId}
            name={company.name}
            logoUrl={company.logo_url ?? null}
            editable
            large
          />
          <div className="space-y-1">
            <h2 className="font-heading text-2xl font-medium">
              {t("logoTitle")}
            </h2>
            <p className="text-muted-foreground">{t("logoText")}</p>
          </div>
        </section>
        <BrandColorsForm
          companyId={companyId}
          saved={company.brand_colors ?? null}
          current={company.candidate_colors}
          style={company.brand_style ?? prepza.style}
          prepza={prepza}
        />
      </CompanyHeader>
    </main>
  )
}
