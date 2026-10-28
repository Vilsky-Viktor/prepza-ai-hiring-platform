import { LinkView } from "@/components/company/link-view"
import { PausedNotice } from "@/components/common/paused-notice"
import { isPaused } from "@/lib/pause"
import { translatedTitle } from "@/lib/site"
import { START_PAGE } from "@/config/start-page"

export const generateMetadata = () => translatedTitle("invite", "title")

/** A test's shareable link, as a company puts it in a job ad; laid out like an invite. */
export default async function ApplyPage({
  params,
}: {
  params: Promise<{ token: string }>
}) {
  const { token } = await params

  return (
    <main className={START_PAGE}>
      <PausedNotice paused={await isPaused()} className="mb-10 w-full" />
      <LinkView token={token} />
    </main>
  )
}
