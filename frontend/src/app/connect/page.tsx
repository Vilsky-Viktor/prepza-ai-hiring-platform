import { ConnectView } from "@/features/connect/components/connect-view"
import { translatedTitle } from "@/lib/site"
import { PageKey } from "@/components/common/page-key"

export const generateMetadata = () => translatedTitle("connect", "pageTitle")

/** An AI app sends the user here to allow or deny it the use of their account
 * (`?request=` names the app's request, kept by the API for a few minutes). */
export default async function ConnectPage({
  searchParams,
}: {
  searchParams: Promise<{ request?: string }>
}) {
  const { request } = await searchParams

  return (
    <main className="mx-auto flex w-full max-w-page flex-1 flex-col items-center justify-center px-6 py-12">
      <PageKey page="connect" />
      <ConnectView requestId={request ?? ""} />
    </main>
  )
}
