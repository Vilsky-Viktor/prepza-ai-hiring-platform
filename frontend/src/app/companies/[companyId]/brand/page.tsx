import { cookies } from "next/headers"
import { redirect } from "next/navigation"
import { getTranslations } from "next-intl/server"

import { BrandColorsForm } from "@/features/company/components/brand-colors-form"
import { CompanyHeader } from "@/features/company/components/company-header"
import { LogoPicker } from "@/features/company/components/logo-picker"
import { SignInPrompt } from "@/components/common/sign-in-prompt"
import { TOKEN_COOKIE } from "@/config/auth"
import { serverFetch } from "@/lib/server-api"
import { translatedTitle } from "@/lib/site"
import { companyHeaderProps } from "@/lib/company-header"
import type { Company, PrepzaBrand } from "@/types/company"

export const generateMetadata = () => translatedTitle("company", "brand")

/** How the company's candidates see its interviews: its logo, and its colors on their
 * invitation, questions and finished page: its general page (logo, font, rounding), then a page
 * for each theme's colors (`?page=light`, `?page=dark`). Owners and admins only, like billing. */
export default async function BrandPage({
  params,
  searchParams,
}: {
  params: Promise<{ companyId: string }>
  searchParams: Promise<{ page?: string }>
}) {
  const { companyId } = await params
  const asked = (await searchParams).page
  const page = asked === "light" || asked === "dark" ? asked : "general"
  const href = `/companies/${companyId}/brand`
  const t = await getTranslations("brand")
  const signedIn = (await cookies()).has(TOKEN_COOKIE)

  if (!signedIn) {
    return (
      <main className="mx-auto max-w-page px-6 py-12">
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
    <main className="mx-auto max-w-page space-y-12 px-6 py-12">
      <CompanyHeader
        {...companyHeaderProps(company)}
        companyId={companyId}
        current="brand"
        // Brand's pages in the menu: the logo, font and rounding, then each theme's colors.
        sub={[
          { id: "general", href, label: t("general") },
          { id: "light", href: `${href}?page=light`, label: t("themes.light") },
          { id: "dark", href: `${href}?page=dark`, label: t("themes.dark") },
        ]}
        currentSub={page}
        className="space-y-12"
      >
        {page === "general" && (
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
        )}
        <BrandColorsForm
          companyId={companyId}
          saved={company.brand_colors ?? null}
          current={company.candidate_colors}
          style={company.brand_style ?? prepza.style}
          prepza={prepza}
          page={page}
        />
      </CompanyHeader>
    </main>
  )
}
