import { headers } from "next/headers"
import { getTranslations } from "next-intl/server"

import { WarningCard } from "@/components/warning-card"
import { MAINTENANCE_HEADER } from "@/constants/maintenance"

/** While maintenance mode is on, superadmins still see the site, with a warning card above
 * every page saying so (WarningCard); otherwise
 * nothing. Its negative bottom margin takes the page's top padding (py-12) down to the gap
 * between a title and what's right under it (space-y-4). */
export async function MaintenanceNotice() {
  if ((await headers()).get(MAINTENANCE_HEADER) !== "open") {
    return null
  }

  const t = await getTranslations("maintenance")

  return (
    <div
      data-testid="maintenance-notice"
      className="mx-auto -mb-8 max-w-page px-6 pt-6"
    >
      <WarningCard>{t("notice")}</WarningCard>
    </div>
  )
}
