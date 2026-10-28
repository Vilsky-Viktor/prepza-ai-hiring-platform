import { StatsView } from "@/features/superadmin/components/stats-view"
import { SuperadminHeader } from "@/features/superadmin/components/superadmin-header"
import { translatedTitle } from "@/lib/site"

export const generateMetadata = () => translatedTitle("superadmin", "zone")

/** The admin zone's stats, all time or for a year or month the superadmin picks; the browser
 * keeps the choice (features/superadmin/components/stats-view.tsx). The API answers superadmins
 * only. */
export default async function StatsPage() {
  return (
    <main className="mx-auto max-w-page space-y-8 px-6 py-12">
      <SuperadminHeader current="stats" sub="general">
        <StatsView />
      </SuperadminHeader>
    </main>
  )
}
