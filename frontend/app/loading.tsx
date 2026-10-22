import { getTranslations } from "next-intl/server"

import { LoadingSpinner } from "@/components/loading-spinner"

/** What a page shows at once while its data loads (a sleeping service can take seconds): the
 * site's header and footer stay, and the page's place has the spinner link pages show. */
export default async function Loading() {
  const common = await getTranslations("common")

  return (
    <main className="mx-auto max-w-page px-6">
      <LoadingSpinner label={common("loading")} />
    </main>
  )
}
