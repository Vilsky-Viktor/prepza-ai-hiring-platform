import { useTranslations } from "next-intl"

import { INVITE_EXAMPLE_LINES } from "@/constants/invites"
import { CARD } from "@/constants/cards"

/** How a list is written, in the gray info card: the hint (with the most a list may hold, when
 * known), then example lines. */
export function InviteExample({ maxInvites }: { maxInvites: number | null }) {
  const t = useTranslations("interviews")

  return (
    <div className={`space-y-2 ${CARD}`}>
      <h2 className="font-heading text-lg font-medium lowercase">
        {t("example")}
      </h2>
      <p className="text-sm whitespace-pre-line text-muted-foreground">
        {maxInvites === null
          ? t("manyHintNoLimit")
          : t("manyHint", { count: maxInvites })}
      </p>
      <p className="font-mono text-sm break-all whitespace-pre-line text-foreground/80">
        {INVITE_EXAMPLE_LINES.join("\n")}
      </p>
    </div>
  )
}
