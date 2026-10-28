import { redirect } from "next/navigation"

export default async function CandidatesPage({
  params,
}: {
  params: Promise<{ companyId: string; id: string }>
}) {
  const { companyId, id } = await params

  redirect(`/companies/${companyId}/interviews/${id}?tab=candidates`)
}
