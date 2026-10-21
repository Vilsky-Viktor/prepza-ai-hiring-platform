import { BriefcaseBusinessIcon } from "lucide-react"
import { getTranslations } from "next-intl/server"

import { LocalizedLink } from "@/components/localized-link"
import { Button } from "@/components/ui/button"
import { priceValues, visitorCatalog } from "@/lib/catalog"

/** The way from a content page to a first test: the home page, where a job description becomes
 * an interview, signed in or not, with the price per candidate in the visitor's currency. Built
 * like the practice pages' hiring card. */
export async function StartCard() {
  const t = await getTranslations("content")
  const prices = await priceValues(await visitorCatalog())

  return (
    <div className="flex flex-col gap-4 rounded-2xl border p-6 sm:flex-row sm:items-center sm:justify-between">
      <div className="flex items-center gap-4">
        <BriefcaseBusinessIcon
          aria-hidden
          className="size-6 shrink-0 text-primary"
        />
        <div className="space-y-1">
          <p className="text-lg font-medium">{t("startTitle")}</p>
          <p className="text-base text-muted-foreground">{t("startText", prices)}</p>
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
