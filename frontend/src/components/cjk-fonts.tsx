"use client"

import dynamic from "next/dynamic"

/** The Japanese, Chinese and Korean fonts, for pages in those languages: loaded on its own, so
 * their stylesheet comes only with this (constants/cjk-fonts.ts). */
export const CjkFonts = dynamic(() =>
  import("@/constants/cjk-fonts").then(({ CJK_FONT_STYLE }) => {
    function CjkFontStyle() {
      return <style>{CJK_FONT_STYLE}</style>
    }

    return CjkFontStyle
  })
)
