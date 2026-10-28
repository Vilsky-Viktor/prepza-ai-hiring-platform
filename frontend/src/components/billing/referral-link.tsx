import { CopyField } from "@/components/copy-field"

/** The company's referral link, opening `path` with its code, to copy. */
export function ReferralLink({
  referral,
  path,
}: {
  referral: { code: string }
  path: string
}) {
  return <CopyField path={`${path}?ref=${referral.code}`} />
}
