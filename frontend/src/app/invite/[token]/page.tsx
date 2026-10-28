import { translatedTitle } from "@/lib/site"
import { InviteView } from "@/components/company/invite-view"
import { PausedNotice } from "@/components/paused-notice"
import { isPaused } from "@/lib/pause"
import { START_PAGE } from "@/constants/start-page"

export const generateMetadata = () => translatedTitle("invite", "title")

export default async function InvitePage({
  params,
}: {
  params: Promise<{ token: string }>
}) {
  const { token } = await params

  return (
    <main className={START_PAGE}>
      <PausedNotice paused={await isPaused()} className="mb-10 w-full" />
      <InviteView token={token} />
    </main>
  )
}
