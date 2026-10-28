import { SuperadminHeader } from "@/components/superadmin/superadmin-header"
import { SupportSearch } from "@/components/superadmin/support-search"
import { translatedTitle } from "@/lib/site"

export const generateMetadata = () => translatedTitle("superadmin", "zone")

/** The admin zone's support tab: finds what a complaint is about, to look into a company's
 * credits, interviews and members. The API answers superadmins only. */
export default function SupportPage() {
  return (
    <main className="mx-auto max-w-page space-y-8 px-6 py-12">
      <SuperadminHeader current="support">
        <SupportSearch />
      </SuperadminHeader>
    </main>
  )
}
