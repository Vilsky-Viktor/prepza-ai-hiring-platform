import { getTranslations } from "next-intl/server"

import { InfoCard } from "@/components/warning-card"

/** While prepza is paused (the admin zone's emergency pause, from isPaused), the gray info card
 * says so; otherwise nothing. */
export async function PausedNotice({
  paused,
  className,
}: {
  paused: boolean
  className?: string
}) {
  const t = await getTranslations("pause")

  if (!paused) {
    return null
  }

  return (
    <div data-testid="paused-notice" className={className}>
      <InfoCard>{t("notice")}</InfoCard>
    </div>
  )
}
