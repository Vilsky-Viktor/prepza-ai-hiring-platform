import { EmbedView } from "@/features/company/components/embed-view"
import { originOf } from "@/lib/embed"
import { translatedTitle } from "@/lib/site"

export const generateMetadata = () => translatedTitle("invite", "title")

export default async function EmbeddedPage({
  params,
  searchParams,
}: {
  params: Promise<{ token: string }>
  searchParams: Promise<{ origin?: string | string[] }>
}) {
  const { token } = await params
  const { origin } = await searchParams

  return (
    <main className="mx-auto w-full max-w-page px-6">
      <EmbedView token={token} origin={originOf(origin)} />
    </main>
  )
}
