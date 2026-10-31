import { cn } from "cn"

import { KeepAcronyms } from "@/components/common/keep-acronyms"
import { FeatureShot } from "@/features/features/components/feature-shot"
import { DOT_CLASS } from "@/config/dot"
import type { FeatureShotName } from "@/config/features-shots"

/** One feature: its title ending with the logo's blue dot, a short text and its points, beside
 * a picture of the real app. From laptops up side by side, the picture on the end side, or the
 * start side when `flip`, so rows alternate; on smaller screens the text above the picture. */
export function FeatureRow({
  title,
  text,
  points,
  shot,
  alt,
  flip = false,
  extra,
}: {
  title: string
  text: string
  points: string[]
  shot: FeatureShotName
  alt: string
  flip?: boolean
  // Under the points: the logos of what it works with.
  extra?: React.ReactNode
}) {
  return (
    // The picture's column is the wider on either side.
    <div
      className={cn(
        "grid items-center gap-8 lg:gap-16",
        flip
          ? "lg:grid-cols-[minmax(0,3fr)_minmax(0,2fr)]"
          : "lg:grid-cols-[minmax(0,2fr)_minmax(0,3fr)]"
      )}
    >
      <div className={cn("space-y-5", flip && "lg:order-last")}>
        <h3 className="font-heading text-2xl font-medium lowercase sm:text-3xl">
          <KeepAcronyms text={title} />
          <span className="blue-dot">.</span>
        </h3>
        <p className="text-lg leading-relaxed text-muted-foreground">{text}</p>
        <ul className="space-y-2 text-base text-muted-foreground">
          {points.map((point) => (
            <li key={point} className="flex gap-3">
              {/* The blue dot centred on the point's first line. */}
              <span aria-hidden className={`${DOT_CLASS} mx-0 mt-[0.53rem]`} />
              {point}
            </li>
          ))}
        </ul>
        {extra}
      </div>
      <FeatureShot name={shot} alt={alt} />
    </div>
  )
}
