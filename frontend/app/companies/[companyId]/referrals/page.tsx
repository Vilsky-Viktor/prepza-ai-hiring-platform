import { GiftIcon } from "lucide-react"
import { cookies } from "next/headers"
import { redirect } from "next/navigation"
import { getTranslations } from "next-intl/server"

import { ReferralLink } from "@/components/billing/referral-link"
import { CompanyHeader } from "@/components/company/company-header"
import { SignInPrompt } from "@/components/sign-in-prompt"
import { TOKEN_COOKIE } from "@/constants/auth"
import { LocalDate } from "@/components/local-date"
import { serverFetch } from "@/lib/server-api"
import { translatedTitle } from "@/lib/site"
import { companyHeaderProps } from "@/lib/company-header"
import type { Company, CompanyReferral } from "@/types/company"
import { LIST_BOX } from "@/constants/lists"

export const generateMetadata = () => translatedTitle("company", "referrals")

export default async function ReferralsPage({
  params,
}: {
  params: Promise<{ companyId: string }>
}) {
  const { companyId } = await params
  const referralText = await getTranslations("referral")
  const signedIn = (await cookies()).has(TOKEN_COOKIE)
  // Asked together: the API refuses the referral on its own when the company isn't theirs.
  const [company, referral] = signedIn
    ? await Promise.all([
        serverFetch<Company>(`/companies/companies/${companyId}`),
        serverFetch<CompanyReferral>(
          `/companies/companies/${companyId}/referral`
        ),
      ])
    : [null, null]

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

  return (
    <main className="mx-auto max-w-page space-y-8 px-6 py-12">
      <CompanyHeader
        {...companyHeaderProps(company)}
        companyId={companyId}
        current="referrals"
      >
        {referral && (
          <>
            {/* What a referral earns, and the link to share; on phones the card spans the screen,
              with square corners. */}
            <div className="-mx-6 space-y-4 border-y p-5 sm:mx-0 sm:rounded-2xl sm:border">
              <div className="flex items-center gap-4 text-base">
                <GiftIcon
                  aria-hidden
                  className="size-7 shrink-0 text-primary"
                />
                <p className="text-muted-foreground">
                  {referralText("companyNote", { reward: referral.reward })}
                </p>
              </div>
              <ReferralLink referral={referral} path="/companies" />
            </div>
            {referral.rewards.length === 0 ? (
              <p className="py-16 text-center text-muted-foreground">
                {referralText("rewarded", { count: 0 })}
              </p>
            ) : (
              <ul className={LIST_BOX}>
                {referral.rewards.map((reward, index) => (
                  <li
                    key={index}
                    className="flex items-center justify-between gap-4 p-6"
                  >
                    <span className="min-w-0 space-y-1">
                      <span className="block truncate text-lg font-medium normal-case">
                        {reward.name ?? referralText("deletedCompany")}
                      </span>
                      <span className="block text-sm text-muted-foreground">
                        <LocalDate iso={reward.rewarded_at} />
                      </span>
                    </span>
                    <span className="shrink-0 text-primary tabular-nums">
                      {referralText("credits", { count: reward.credits })}
                    </span>
                  </li>
                ))}
              </ul>
            )}
          </>
        )}
      </CompanyHeader>
    </main>
  )
}
