import { AiCostsView } from "@/features/superadmin/components/ai-costs-view"
import { SuperadminHeader } from "@/features/superadmin/components/superadmin-header"
import { translatedTitle } from "@/lib/site"

export const generateMetadata = () => translatedTitle("superadmin", "zone")

/** The stats tab's AI costs: what AI cost in a year or month the superadmin picks (general's
 * choice too) and why, the shared budgets today, and who hits which limit. The API answers
 * superadmins only. */
export default async function AiCostsPage() {
  return (
    <main className="mx-auto max-w-page space-y-8 px-6 py-12">
      <SuperadminHeader current="stats" sub="ai-costs">
        <AiCostsView />
      </SuperadminHeader>
    </main>
  )
}
