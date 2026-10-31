import { ATS_PROVIDERS } from "@/config/ats"

/** The ATSs a company connects, by their full logos in the text's colour (black, or white in
 * dark), so they read as one row; each named by its alt text. */
export function FeatureLogos() {
  return (
    <ul className="flex flex-wrap items-center gap-x-8 gap-y-4 pt-1">
      {ATS_PROVIDERS.map((provider) => (
        <li key={provider.id}>
          {/* A small fixed-size logo: a plain image (.claude/rules/performance.md). */}
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img
            src={provider.wordmark}
            alt={provider.name}
            className="h-6 w-auto brightness-0 dark:invert"
          />
        </li>
      ))}
    </ul>
  )
}
