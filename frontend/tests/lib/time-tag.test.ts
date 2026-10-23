import { NextIntlClientProvider, useTranslations } from "next-intl"
import { createElement } from "react"
import { renderToStaticMarkup } from "react-dom/server"
import { describe, expect, it } from "vitest"

import { useLocalTime } from "@/hooks/use-local-time"
import { timeTag } from "@/lib/time-tag"

const MOMENT = "2026-10-01T23:30:00Z"

describe("timeTag", () => {
  it("puts a message's date in a <time> element naming its moment", () => {
    const element = timeTag("2026-10-08").time("Oct 8, 2026")

    expect(renderToStaticMarkup(element)).toBe(
      '<time dateTime="2026-10-08">Oct 8, 2026</time>'
    )
  })
})

describe("useLocalTime's dateValues", () => {
  // Rendered as the server renders it: in UTC, in the page's language.
  function rendered(locale: string, message: string) {
    function Sentence() {
      const t = useTranslations()

      return t.rich("made", useLocalTime().dateValues(MOMENT))
    }

    return renderToStaticMarkup(
      createElement(
        NextIntlClientProvider,
        { locale, messages: { made: message }, timeZone: "UTC" },
        createElement(Sentence)
      )
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
