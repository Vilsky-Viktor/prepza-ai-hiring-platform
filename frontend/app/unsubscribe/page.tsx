import { translatedTitle } from "@/lib/site"
import { UnsubscribeView } from "@/components/unsubscribe-view"
import { PageKey } from "@/components/page-key"

export const generateMetadata = () => translatedTitle("unsubscribe", "title")

/** An email's unsubscribe link opens here, signed in or not. */
export default async function UnsubscribePage({
  searchParams,
}: {
  searchParams: Promise<{ token?: string }>
}) {
  const { token } = await searchParams

  return (
    <main className="mx-auto flex w-full max-w-page flex-1 flex-col items-center justify-center px-6 py-12">
      <PageKey page="unsubscribe" />
      <UnsubscribeView token={token ?? ""} />
    </main>
  )
}
