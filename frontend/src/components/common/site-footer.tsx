import { getTranslations } from "next-intl/server"

import {
  FacebookIcon,
  LinkedInIcon,
  XIcon,
  YouTubeIcon,
} from "@/components/icons/brand-icons"
import { AskAgentButton } from "@/components/landing/ask-agent-button"
import { LanguageSwitch } from "@/components/common/language-switch"
import { LocalizedLink } from "@/components/common/localized-link"
import { FOOTER_COLUMNS } from "@/config/navigation"
import { OPERATOR } from "@/config/operator"

// A social icon: the text colour (white in dark) and a little larger on hover.
const SOCIAL =
  "inline-flex transition-[color,scale] duration-200 hover:scale-110 hover:text-foreground"

export async function SiteFooter() {
  const t = await getTranslations("nav")

  return (
    <footer className="border-t">
      {/* On phones: everything centered in one column, with bigger icons, button and links. */}
      <div className="mx-auto flex max-w-page flex-wrap justify-between gap-8 px-6 py-8 text-sm text-muted-foreground max-sm:flex-col max-sm:items-center max-sm:gap-10 max-sm:py-12 max-sm:text-center sm:gap-x-16">
        <div className="space-y-6 max-sm:flex max-sm:flex-col max-sm:items-center">
          {/* The legal operator, as EU rules want it within reach of every page. */}
          {/* The language menu sits beside it, wrapping under it on narrow phones. */}
          <div className="flex flex-wrap items-center gap-x-4 gap-y-2 max-sm:justify-center">
            <span>
              © {new Date().getFullYear()} {OPERATOR.name}
            </span>
            <LanguageSwitch />
          </div>
          {/* prepza's social accounts; links come once the accounts exist. */}
          <div className="flex items-center gap-5 max-sm:gap-8">
            <span role="img" aria-label="LinkedIn" className={SOCIAL}>
              <LinkedInIcon className="size-6 max-sm:size-8" />
            </span>
            <span role="img" aria-label="X" className={SOCIAL}>
              <XIcon className="size-6 max-sm:size-8" />
            </span>
            <span role="img" aria-label="YouTube" className={SOCIAL}>
              <YouTubeIcon className="size-6 max-sm:size-8" />
            </span>
            <span role="img" aria-label="Facebook" className={SOCIAL}>
              <FacebookIcon className="size-6 max-sm:size-8" />
            </span>
          </div>
          <AskAgentButton className="h-10 px-5 text-sm max-sm:h-12 max-sm:px-6 max-sm:text-base" />
        </div>
        {/* Lowercase with the blue dot, like the header's menu (globals.css, by data-slot). */}
        <nav
          data-slot="footer-nav"
          aria-label={t("footer")}
          className="grid grid-cols-3 gap-x-6 [overflow-wrap:anywhere] hyphens-auto max-sm:grid-cols-1 max-sm:gap-y-3 max-sm:text-lg sm:max-w-3xl sm:min-w-0 sm:flex-1 sm:grid-cols-[repeat(3,auto)] sm:justify-between sm:gap-x-6 lg:gap-x-10"
        >
          {FOOTER_COLUMNS.map((column) => (
            <ul key={column[0].href} className="space-y-2 max-sm:space-y-3">
              {column.map((link) => (
                <li key={link.href}>
                  <LocalizedLink
                    href={link.href}
                    className="-mx-1.5 rounded-lg px-1.5 py-0.5 transition-colors hover:text-foreground active:bg-surface active:text-foreground"
                  >
                    {t(link.label)}
                  </LocalizedLink>
                </li>
              ))}
            </ul>
          ))}
        </nav>
      </div>
    </footer>
  )
}
