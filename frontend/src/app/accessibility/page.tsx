import { getLocale, getTranslations } from "next-intl/server"

import {
  ACCESSIBILITY_DONE,
  ACCESSIBILITY_LIMITS,
  ACCESSIBILITY_REVIEWED,
} from "@/config/accessibility"
import { OPERATOR } from "@/config/operator"
import { formatDay } from "@/lib/format"
import { pageMetadata } from "@/lib/site"
import { timeTag } from "@/lib/time-tag"
import { BackLink } from "@/components/common/back-link"
import { BulletSection } from "@/components/common/bullet-section"
import { PageKey } from "@/components/common/page-key"

export async function generateMetadata() {
  const t = await getTranslations("accessibility")

  return pageMetadata(t("title"), t("description"), "/accessibility", true)
}

/** The accessibility statement: what prepza does for people with disabilities, what falls
 * short, and how to tell us. */
export default async function AccessibilityPage() {
  const t = await getTranslations("accessibility")
  const locale = await getLocale()

  return (
    <main className="mx-auto max-w-page space-y-12 px-6 py-12">
      <PageKey page="accessibility" />
      <header className="mx-auto max-w-5xl space-y-4">
        {/* The way back home, beside the title as on the app's pages. */}
        <div className="relative">
          <BackLink href="/">{null}</BackLink>
          <h1 className="font-heading text-4xl font-medium tracking-tight">
            {t("title")}
          </h1>
        </div>
        <p className="text-lg text-muted-foreground">{t("intro")}</p>
      </header>
      <BulletSection
        title={t("done.title")}
        items={ACCESSIBILITY_DONE.map((key) => t(`done.${key}`))}
      />
      <BulletSection
        title={t("limits.title")}
        items={ACCESSIBILITY_LIMITS.map((key) => t(`limits.${key}`))}
      />
      <section className="mx-auto max-w-5xl space-y-4">
        <h2 className="font-heading text-2xl font-medium tracking-tight">
          {t("feedback.title")}
        </h2>
        <p className="text-base leading-relaxed text-muted-foreground">
          {t.rich("feedback.text", {
            email: () => (
              <a
                href={`mailto:${OPERATOR.email}`}
                className="text-foreground underline"
              >
                {OPERATOR.email}
              </a>
            ),
          })}
        </p>
        <p className="text-base leading-relaxed text-muted-foreground">
          {t("feedback.authority")}
        </p>
      </section>
      <p className="mx-auto max-w-5xl text-sm text-muted-foreground">
        {t.rich("reviewed", {
          date: formatDay(ACCESSIBILITY_REVIEWED, locale),
          ...timeTag(ACCESSIBILITY_REVIEWED),
        })}
      </p>
    </main>
  )
}
