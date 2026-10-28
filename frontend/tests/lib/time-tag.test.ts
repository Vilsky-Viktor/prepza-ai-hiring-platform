import { NextIntlClientProvider, useTranslations } from "next-intl"
import { type ComponentProps, createElement, type ReactNode } from "react"
import { renderToStaticMarkup } from "react-dom/server"
import { describe, expect, it } from "vitest"

import type { Locale } from "@/config/i18n"
import { useLocalTime } from "@/hooks/use-local-time"
import { timeTag } from "@/lib/time-tag"

const MOMENT = "2026-10-01T23:30:00Z"

type Rich = { rich: (key: string, values: object) => ReactNode }
type Provider = ComponentProps<typeof NextIntlClientProvider>

describe("timeTag", () => {
  it("puts a message's date in a <time> element naming its moment", () => {
    const element = timeTag("2026-10-08").time("Oct 8, 2026")

    expect(renderToStaticMarkup(element)).toBe(
      '<time dateTime="2026-10-08">Oct 8, 2026</time>'
    )
  })
})

describe("useLocalTime's dateValues", () => {
  // Rendered as the server renders it: in UTC, in the page's language. The test's one-message
  // catalogue isn't the app's typed messages, so its key and messages are cast.
  function rendered(locale: Locale, message: string) {
    function Sentence() {
      const t = useTranslations() as unknown as Rich

      return t.rich("made", useLocalTime().dateValues(MOMENT))
    }

    const props = {
      locale,
      messages: { made: message },
      timeZone: "UTC",
    } as unknown as Provider

    return renderToStaticMarkup(
      createElement(NextIntlClientProvider, props, createElement(Sentence))
    )
  }

  it("fills a message's <time> tag with the moment's date", () => {
    expect(rendered("en", "made <time>{date}</time>")).toBe(
      'made <time dateTime="2026-10-01T23:30:00Z">Oct 1, 2026</time>'
    )
  })

  it("writes the date as the language does", () => {
    expect(rendered("de", "erstellt am <time>{date}</time>")).toBe(
      'erstellt am <time dateTime="2026-10-01T23:30:00Z">01.10.2026</time>'
    )
  })
})
