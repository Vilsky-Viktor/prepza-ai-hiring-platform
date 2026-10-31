import { IconCard, PHONE_CARDS } from "@/components/common/icon-card"
import type { FeatureCard } from "@/config/features-page"

/** A group's smaller features as the landing's grey cards: three to a row from laptops up, two
 * on tablets, one under another edge to edge on phones; on a grey band, in the page's colour. */
export function FeatureCards({
  cards,
  onBand,
}: {
  cards: (FeatureCard & { title: string; text: string })[]
  onBand: boolean
}) {
  return (
    <ul className={`grid gap-3 sm:grid-cols-2 lg:grid-cols-3 ${PHONE_CARDS}`}>
      {cards.map((card) => (
        <IconCard
          key={card.key}
          icon={card.icon}
          title={card.title}
          className={onBand ? "bg-background" : undefined}
        >
          {card.text}
        </IconCard>
      ))}
    </ul>
  )
}
