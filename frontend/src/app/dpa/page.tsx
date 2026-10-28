import { LegalPage } from "@/components/legal-page"
import { pageMetadata } from "@/lib/site"

export const generateMetadata = () =>
  pageMetadata(
    "Data processing agreement",
    "The data processing agreement between prepza and companies that test candidates: what prepza processes on your behalf and how.",
    "/dpa"
  )

export default async function DpaPage({
  searchParams,
}: {
  searchParams: Promise<{ version?: string; language?: string }>
}) {
  const { version, language } = await searchParams

  return <LegalPage name="dpa" version={version} english={language === "en"} />
}
