import { LegalPage } from "@/components/legal-page"
import { pageMetadata } from "@/lib/site"

export const generateMetadata = () =>
  pageMetadata(
    "Terms of service",
    "The terms for using prepza: accounts, companies, credits and payments, tests for candidates, acceptable use and liability.",
    "/terms"
  )

export default async function TermsPage({
  searchParams,
}: {
  searchParams: Promise<{ version?: string; language?: string }>
}) {
  const { version, language } = await searchParams

  return (
    <LegalPage name="terms" version={version} english={language === "en"} />
  )
}
