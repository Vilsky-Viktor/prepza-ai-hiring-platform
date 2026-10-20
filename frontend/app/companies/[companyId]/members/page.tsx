import { cookies } from "next/headers"
import { redirect } from "next/navigation"

import { CompanyHeader } from "@/components/company/company-header"
import { InviteAdmin } from "@/components/company/invite-admin"
import { MemberList } from "@/components/company/member-list"
import { SignInPrompt } from "@/components/sign-in-prompt"
import { TOKEN_COOKIE } from "@/constants/auth"
import { PAGE_SIZE } from "@/constants/lists"
import { serverFetch } from "@/lib/server-api"
import { translatedTitle } from "@/lib/site"
import { companyHeaderProps } from "@/lib/company-header"
import type { Company, CompanyMember } from "@/types/company"

export const generateMetadata = () => translatedTitle("company", "team")

export default async function MembersPage({
  params,
}: {
  params: Promise<{ companyId: string }>
}) {
  const { companyId } = await params
  const signedIn = (await cookies()).has(TOKEN_COOKIE)
  const company = signedIn
    ? await serverFetch<Company>(`/companies/companies/${companyId}`)
    : null
  const members = company
    ? await serverFetch<CompanyMember[]>(
        `/companies/members?company_id=${companyId}&limit=${PAGE_SIZE}`
      )
    : null

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
        current="members"
        action={
          company.can_manage_members ? (
            <InviteAdmin companyId={companyId} />
          ) : undefined
        }
      />
      <MemberList companyId={companyId} initial={members ?? []} />
    </main>
  )
}
