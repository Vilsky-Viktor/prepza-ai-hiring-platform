import { LinkIcon } from "lucide-react"
import { getTranslations } from "next-intl/server"
import { cn } from "cn"

import { CopyField } from "@/components/common/copy-field"
import { CornerSign } from "@/components/common/corner-sign"
import { SIGN_CARD } from "@/config/cards"

/** The invite link until the interview is finished, in case the email didn't reach the
 * candidate or they lost it. */
export async function InviteLinkCard({ token }: { token?: string | null }) {
  const t = await getTranslations("candidates")

  if (!token) {
    return null
  }

  return (
    <div
      className={cn(SIGN_CARD, "space-y-4 max-sm:-mx-6 max-sm:rounded-none")}
    >
      <CornerSign>
        <LinkIcon className="text-primary" />
      </CornerSign>
      <div className="flex items-center gap-4 text-base">
        <div className="min-w-0 flex-1 space-y-1">
          <p className="font-medium lowercase">{t("inviteLinkTitle")}</p>
          <p className="text-sm text-muted-foreground">{t("inviteLinkHint")}</p>
        </div>
      </div>
      <CopyField path={`/invite/${token}`} />
    </div>
  )
}
