import { cn } from "cn"
import { DownloadIcon } from "lucide-react"
import { getTranslations } from "next-intl/server"

import { DEMO_BAND } from "@/components/landing/demo-panel"
import { ReportsDemo } from "@/components/landing/reports-demo"
import { LandingSection, OUTLINE_BUTTON } from "@/components/landing/section"
import { StartButton } from "@/components/landing/start-button"
import { buttonVariants } from "@/components/ui/button"
import { REPORT_SAMPLES_URL } from "@/constants/report-samples"

/** Detailed reports and quick sharing: the candidates list and a candidate's report, each
 * shared, played in one panel; then the button to create an interview and, beside it, the
 * sample reports to download. On phones they stack, as wide as each other. */
export async function ShareReportsSection() {
  const t = await getTranslations("landing")

  return (
    <LandingSection
      id="reports"
      title={t("shareReports.title")}
      text={t("shareReports.text")}
    >
      <div className={DEMO_BAND}>
        <ReportsDemo />
      </div>
      <div className="flex justify-center gap-3 max-sm:mx-auto max-sm:w-fit max-sm:flex-col max-sm:items-stretch">
        <StartButton label={t("closing.start")} />
        {/* A ZIP of the two PDF reports, saved rather than opened: a browser can't show a ZIP. */}
        <a
          href={REPORT_SAMPLES_URL}
          download
          data-testid="report-samples"
          className={cn(
            buttonVariants({ variant: "outline" }),
            OUTLINE_BUTTON,
            "h-14 px-10 text-lg lowercase"
          )}
        >
          <DownloadIcon aria-hidden className="size-5" />
          {t("shareReports.samples")}
        </a>
      </div>
    </LandingSection>
  )
}
