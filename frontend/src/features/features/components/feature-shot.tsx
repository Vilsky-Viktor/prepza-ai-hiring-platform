import Image from "next/image"

import {
  FEATURE_SHOTS,
  FEATURE_SHOTS_PATH,
  type FeatureShotName,
} from "@/config/features-shots"

// Shown at most about 45rem wide beside its text from laptops up; the screen's width below.
const SIZES = "(min-width: 1024px) 45rem, 100vw"

/** A picture of the real app in a bordered frame like the landing's pictures, its light or dark
 * version as the page's theme is: the other is hidden, so the browser never loads it (both are
 * lazy). On phones, edge to edge. */
export function FeatureShot({
  name,
  alt,
}: {
  name: FeatureShotName
  alt: string
}) {
  const { width, height } = FEATURE_SHOTS[name]

  return (
    <div className="rounded-xl border bg-background p-2 max-sm:-mx-6 max-sm:rounded-none max-sm:border-x-0 sm:p-3">
      <Image
        src={`${FEATURE_SHOTS_PATH}/${name}-light.webp`}
        width={width}
        height={height}
        alt={alt}
        sizes={SIZES}
        className="h-auto w-full rounded-lg dark:hidden"
      />
      <Image
        src={`${FEATURE_SHOTS_PATH}/${name}-dark.webp`}
        width={width}
        height={height}
        alt={alt}
        sizes={SIZES}
        className="hidden h-auto w-full rounded-lg dark:block"
      />
    </div>
  )
}
