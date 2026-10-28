import { CARD } from "@/constants/cards"

/** Numbers as cards, three to a row and centred, like the pricing cards: each its label under a
 * large number. The admin zone's stats and a campaign's counts. */
export function NumberCards({
  items,
}: {
  items: { key: string; label: string; value: string }[]
}) {
  return (
    <dl className="flex flex-wrap justify-center gap-4">
      {items.map((item) => (
        <div
          key={item.key}
          data-testid={`number-${item.key}`}
          className={`flex w-full flex-col-reverse gap-1 ${CARD} text-center sm:w-[calc((100%-1rem)/2)] lg:w-[calc((100%-2rem)/3)]`}
        >
          <dt className="text-sm text-muted-foreground">{item.label}</dt>
          <dd className="font-heading text-5xl font-medium tracking-tight text-primary tabular-nums">
            {item.value}
          </dd>
        </div>
      ))}
    </dl>
  )
}
