import { cn } from "cn"
import { BriefcaseBusinessIcon } from "lucide-react"
import { getTranslations } from "next-intl/server"

import { CornerSign } from "@/components/corner-sign"
import { LocalizedLink } from "@/components/localized-link"
import { Button } from "@/components/ui/button"
import { priceValues, visitorCatalog } from "@/lib/catalog"
import { SIGN_CARD } from "@/constants/cards"

/** The way from a content page to a first test: the home page, where a job description becomes
 * an interview, signed in or not, with the price per candidate in the visitor's currency. Built
 * like the practice pages' hiring card. */
export async function StartCard() {
  const t = await getTranslations("content")
  const prices = await priceValues(await visitorCatalog())

  return (
    <div
      data-testid="start-card"
      className={cn(
        SIGN_CARD,
        "flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between"
      )}
    >
      <CornerSign>
        <BriefcaseBusinessIcon className="text-primary" />
      </CornerSign>
      <div className="flex items-center gap-4">
        <div className="space-y-1">
          <p className="text-lg font-medium">{t("startTitle")}</p>
          <p className="text-base text-muted-foreground">
            {t("startText", prices)}
          </p>
        </div>
      </div>
      <Button
        className="h-10 shrink-0 px-5 text-base"
        render={<LocalizedLink href="/" />}
        nativeButton={false}
      >
        {t("startButton")}
      </Button>
    </div>
  )
}
