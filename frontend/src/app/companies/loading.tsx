import { getTranslations } from "next-intl/server"

import { LoadingSpinner } from "@/components/common/loading-spinner"

/** What a company's page shows at once while its data loads (companies, billing and the other
 * services it asks can take seconds after idle): the site's header and footer stay, and the
 * page's place has the spinner link pages show. Only here: a loading state streams the page, so a
 * page under it that isn't found answers 200, which these signed-in pages (noindex) can take;
 * public and admin pages keep their real 404. */
export default async function Loading() {
  const common = await getTranslations("common")

  return (
    <main className="mx-auto max-w-page px-6">
      <LoadingSpinner label={common("loading")} />
    </main>
  )
}
