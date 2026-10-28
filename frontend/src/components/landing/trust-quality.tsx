import { getTranslations } from "next-intl/server"

import { KeepAcronyms } from "@/components/keep-acronyms"
import { DEMO_GROUP } from "@/components/landing/demo-panel"
import { QualityLoop } from "@/components/landing/quality-loop"
import { LandingSection } from "@/components/landing/section"
import { LocalizedLink } from "@/components/localized-link"
import {
  QUALITY_STEPS,
  type QualityStep,
  TRUST_CARDS,
} from "@/config/trust-quality-demo"
import { TEXT_LINK } from "@/config/links"

/** Trust, quality and compliance: the loop that keeps questions good, and what keeps the
 * hiring fair and lawful under it, with links to the documents. */
export async function TrustQualitySection() {
  const t = await getTranslations("landing.trustQuality")
  const steps = (part: "labels" | "lines") =>
    Object.fromEntries(
      QUALITY_STEPS.map((key) => [key, t(`steps.${key}.${part}`)])
    ) as Record<QualityStep, string>
  const link = (href: string) =>
    function DocumentLink(chunks: React.ReactNode) {
      return (
        <LocalizedLink href={href} className={TEXT_LINK}>
          {chunks}
        </LocalizedLink>
      )
    }

  return (
    <LandingSection id="trust" title={t("title")} text={t("text")}>
      <div className="flex flex-col gap-14">
        <div className={DEMO_GROUP}>
          <QualityLoop labels={steps("labels")} lines={steps("lines")} />
        </div>
        {/* Four columns side by side from laptops up, split by thin lines; one under another
            below that. */}
        <ul className="grid divide-y lg:grid-cols-4 lg:divide-x lg:divide-y-0">
          {TRUST_CARDS.map((key) => (
            <li
              key={key}
              className="flex flex-col gap-2 py-8 max-lg:first:pt-0 max-lg:last:pb-0 lg:px-8 lg:py-2 lg:first:ps-0 lg:last:pe-0"
            >
              <h3 className="font-heading text-xl font-medium lowercase">
                <KeepAcronyms text={t(`cards.${key}.title`)} />
                <span className="text-primary">.</span>
              </h3>
              <p className="text-base leading-relaxed text-muted-foreground">
                {key === "laws"
                  ? t.rich("cards.laws.text", { documents: link("/documents") })
                  : t(`cards.${key}.text`)}
              </p>
            </li>
          ))}
        </ul>
      </div>
    </LandingSection>
  )
}
