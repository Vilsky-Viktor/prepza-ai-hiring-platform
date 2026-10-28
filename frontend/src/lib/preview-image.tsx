import { readFile } from "node:fs/promises"
import { join } from "node:path"

import { ImageResponse } from "next/og"

import type { Locale } from "@/constants/i18n"
import {
  PREVIEW_COLORS,
  PREVIEW_FALLBACK_FONT,
  PREVIEW_SCRIPT_FONTS,
  PREVIEW_SIZE,
} from "@/constants/preview-image"

// A title's end that takes no blue dot, as with the site's question titles.
const ENDS_IN_PUNCTUATION = /[.?!。？！]$/
// Text Poppins draws by itself: Latin with its accents.
const POPPINS_ONLY = /^[\u0000-\u024f\u2000-\u206f]*$/

/** One of the heading font's files, kept in assets/fonts. */
function font(file: string) {
  return readFile(join(process.cwd(), "assets/fonts", file))
}

/** A Google font with just the letters of `text`, for the ones Poppins lacks; null when Google
 * can't be reached, and the preview draws without them. */
async function googleFont(family: string, text: string) {
  try {
    const css = await (
      await fetch(
        `https://fonts.googleapis.com/css2?family=${encodeURIComponent(family)}:wght@400&text=${encodeURIComponent(text)}`
      )
    ).text()
    const url = css.match(/src: url\((.+?)\)/)?.[1]

    const file = url ? await fetch(url) : null

    // Google answers with a page, not a font, when the family has none of the letters.
    return file?.ok && !file.headers.get("content-type")?.includes("html")
      ? await file.arrayBuffer()
      : null
  } catch {
    return null
  }
}

/** The link preview picture: the logo, centred and large, over the lines of a title in grey,
 * each ending in the logo's blue dot. Words wrap, so a long title takes a few lines. */
export async function drawPreview(lines: string[], locale: Locale = "en") {
  const text = lines.join(" ")
  const family = PREVIEW_SCRIPT_FONTS[locale] ?? PREVIEW_FALLBACK_FONT
  const extra = POPPINS_ONLY.test(text) ? [] : [family]
  const extraFonts = await Promise.all(
    extra.map(async (family) => ({
      name: family,
      data: await googleFont(family, text),
      weight: 400 as const,
    }))
  )

  return new ImageResponse(
    <div
      style={{
        width: "100%",
        height: "100%",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        gap: 32,
        padding: "0 80px",
        background: PREVIEW_COLORS.background,
        fontFamily: ["Poppins", ...extra].join(", "),
        letterSpacing: "-0.025em",
      }}
    >
      {/* The logo, as the Wordmark draws it: semibold. */}
      <div
        style={{
          display: "flex",
          fontSize: 176,
          fontWeight: 600,
          color: PREVIEW_COLORS.logo,
        }}
      >
        prepza<span style={{ color: PREVIEW_COLORS.dot }}>.</span>
      </div>
      {/* The title as the site's headings: regular, grey, lines set tight. */}
      <div
        style={{
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          fontSize: 60,
          fontWeight: 400,
          lineHeight: 1.1,
          color: PREVIEW_COLORS.title,
        }}
      >
        {/* Word by word, so a long title wraps between words and keeps its dot on its last. */}
        {lines.map((line) => {
          const words = line.split(" ")

          return (
            <div
              key={line}
              style={{
                display: "flex",
                flexWrap: "wrap",
                justifyContent: "center",
                columnGap: 16,
              }}
            >
              {words.map((word, index) => (
                <div key={index} style={{ display: "flex" }}>
                  {word}
                  {index === words.length - 1 &&
                    !ENDS_IN_PUNCTUATION.test(line) && (
                      <span style={{ color: PREVIEW_COLORS.dot }}>.</span>
                    )}
                </div>
              ))}
            </div>
          )
        })}
      </div>
    </div>,
    {
      ...PREVIEW_SIZE,
      fonts: [
        {
          name: "Poppins",
          data: await font("Poppins-Regular.ttf"),
          weight: 400,
        },
        {
          name: "Poppins",
          data: await font("Poppins-SemiBold.ttf"),
          weight: 600,
        },
        ...extraFonts.flatMap(({ data, ...rest }) =>
          data ? [{ ...rest, data }] : []
        ),
      ],
    }
  )
}
