import { cn } from "cn"
import { BriefcaseBusinessIcon } from "lucide-react"
import Link from "next/link"
import { getTranslations } from "next-intl/server"

import { CornerSign } from "@/components/common/corner-sign"
import { Button } from "@/components/ui/button"
import { SIGN_CARD } from "@/config/cards"

/** For a hiring manager who found or just took a practice interview: this test for their own
 * candidates, in a company they choose (app/companies/templates). */
export async function HireWithTemplate({ templateId }: { templateId: string }) {
  const t = await getTranslations("practice")

  return (
    <div
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
          <p className="text-lg font-medium">{t("hireTitle")}</p>
          <p className="text-base text-muted-foreground">{t("hireText")}</p>
        </div>
      </div>
      <Button
        className="h-10 shrink-0 px-5 text-base"
        render={<Link href={`/companies/templates/${templateId}`} />}
        nativeButton={false}
      >
        {t("hireButton")}
      </Button>
    </div>
  )
}
