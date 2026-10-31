import { getTranslations } from "next-intl/server"

import { MoreLink } from "@/components/common/more-link"
import { FeatureCards } from "@/features/features/components/feature-cards"
import { FeatureLogos } from "@/features/features/components/feature-logos"
import { FeatureRow } from "@/features/features/components/feature-row"
import { LOCALES } from "@/config/i18n"
import type { FeatureGroup } from "@/config/features-page"

/** What a group of the features page holds under its title: its rows, alternating sides, then
 * its cards and its link onwards. Counts come from the API (`questionsPerTopic`, from
 * generation; `freeCandidates` and `currencies`, from billing); a point or card that needs one is left out
 * without it. */
export async function FeatureGroupBody({
  group,
  questionsPerTopic,
  freeCandidates,
  currencies,
}: {
  group: FeatureGroup
  questionsPerTopic: number | null
  freeCandidates: number | null
  currencies: number | null
}) {
  const t = await getTranslations("featuresPage")
  const counts: Record<string, number | null> = {
    questions: questionsPerTopic,
    languages: LOCALES.length,
    free: freeCandidates,
    currencies,
  }
  const counted = (key: string) => !(key in counts) || counts[key] !== null
  const values = (key: string) => ({ count: counts[key] ?? 0 })

  return (
    <div className="flex flex-col gap-20 sm:gap-24">
      {group.rows.map((row, index) => (
        <FeatureRow
          key={row.key}
          title={t(`rows.${row.key}.title`)}
          text={t(`rows.${row.key}.text`)}
          points={row.points
            .filter(counted)
            .map((point) => t(`points.${point}`, values(point)))}
          shot={row.shot}
          alt={t(`rows.${row.key}.alt`)}
          flip={index % 2 === 1}
          extra={row.logos && <FeatureLogos />}
        />
      ))}
      <div className="flex flex-col items-center gap-10">
        <FeatureCards
          onBand={Boolean(group.background)}
          cards={group.cards
            .filter((card) => counted(card.key))
            .map((card) => ({
              ...card,
              title: t(`cards.${card.key}.title`, values(card.key)),
              text: t(`cards.${card.key}.text`, values(card.key)),
            }))}
        />
        {group.more && (
          <MoreLink href={group.more.href}>
            {t(`more.${group.more.key}`)}
          </MoreLink>
        )}
      </div>
    </div>
  )
}
