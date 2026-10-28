import { Noto_Sans_JP, Noto_Sans_KR, Noto_Sans_SC } from "next/font/google"

// The Japanese, Chinese and Korean fonts: hundreds of character ranges each, so only pages in
// those languages load them (components/cjk-fonts.tsx), keeping them out of every other page's
// stylesheet. As in fonts.ts, next/font reads the options literally: not preloaded.

const japanese = Noto_Sans_JP({ preload: false, display: "swap" })
const chinese = Noto_Sans_SC({ preload: false, display: "swap" })
const korean = Noto_Sans_KR({ preload: false, display: "swap" })

// Their CSS variables, which app/globals.css lists among the script fonts on those pages.
export const CJK_FONT_STYLE = `:root {
  --font-japanese: ${japanese.style.fontFamily};
  --font-chinese: ${chinese.style.fontFamily};
  --font-korean: ${korean.style.fontFamily};
}`
