import { getTranslations } from "next-intl/server"

import { LoadingSpinner } from "@/components/common/loading-spinner"

/** What an interview shows at once after Accept & start, while its page loads: the site's AI
 * loading mark, never a blank screen. */
export default async function Loading() {
  const common = await getTranslations("common")

  return (
    <main className="mx-auto max-w-page px-6">
      <LoadingSpinner label={common("loading")} />
    </main>
  )
}
