import { getTranslations } from "next-intl/server"

import { FeatureGroupBody } from "@/features/features/components/feature-group"
import { FeaturesClosing } from "@/features/features/components/features-closing"
import { FeaturesHero } from "@/features/features/components/features-hero"
import { FeaturesNav } from "@/features/features/components/features-nav"
import { PageKey } from "@/components/common/page-key"
import { LandingSection } from "@/features/landing/components/section"
import { FEATURE_GROUPS } from "@/config/features-page"
import { LOCALES } from "@/config/i18n"
import { visitorCatalog } from "@/lib/catalog"
import { publicFetch } from "@/lib/server-api"
import { pageMetadata } from "@/lib/site"
import type { Sizes } from "@/types/generation"

export async function generateMetadata() {
  const t = await getTranslations("featuresPage")

  return pageMetadata(t("title"), t("description"), "/features", true)
}

/** Every feature, for a company choosing prepza: the promise, the groups as tabs that stay in
 * view, each group a landing section of rows (a text beside a picture of the real app) and
 * cards, and the start box at the end. Counts and prices come from the API, and the page shows
 * without them. */
export default async function FeaturesPage() {
  const t = await getTranslations("featuresPage")
  // Asked together; without an answer the page shows without what needs it.
  const [catalog, sizes] = await Promise.all([
    visitorCatalog(),
    publicFetch<Sizes>("/generate/sizes").catch(() => null),
  ])
  const freeCandidates = catalog?.free_candidates ?? null

  return (
    // As wide as the page's box, for the sections' window-wide backgrounds.
    <div className="@container">
      <main className="mx-auto max-w-page px-6">
        <PageKey page="features" />
        <FeaturesHero />
        <FeaturesNav
          items={FEATURE_GROUPS.map((group) => ({
            id: group.id,
            label: t(`nav.${group.id}`),
          }))}
        />
        {FEATURE_GROUPS.map((group) => (
          <LandingSection
            key={group.id}
            id={group.id}
            title={t(`groups.${group.id}.title`)}
            text={t(`groups.${group.id}.text`, { count: LOCALES.length })}
            background={group.background}
          >
            <FeatureGroupBody
              group={group}
              questionsPerTopic={sizes?.questions_per_topic ?? null}
              freeCandidates={freeCandidates}
              currencies={catalog?.currencies.length ?? null}
            />
          </LandingSection>
        ))}
        <FeaturesClosing freeCandidates={freeCandidates} />
      </main>
    </div>
  )
}
