import { SessionView } from "@/features/company/components/session-view"
import { translatedTitle } from "@/lib/site"

export const generateMetadata = () => translatedTitle("session", "title")

// A company member's preview passes the test it came from; nothing else is accepted.
const FROM_TEST = /^\/companies\/[^/]+\/interviews\/[^/?#]+$/

export default async function SessionPage({
  params,
  searchParams,
}: {
  params: Promise<{ id: string }>
  searchParams: Promise<{ from?: string }>
}) {
  const { id } = await params
  const { from } = await searchParams
  const testHref = from && FROM_TEST.test(from) ? from : undefined

  return (
    <main className="mx-auto max-w-page px-6 py-12">
      <SessionView id={id} testHref={testHref} />
    </main>
  )
}
