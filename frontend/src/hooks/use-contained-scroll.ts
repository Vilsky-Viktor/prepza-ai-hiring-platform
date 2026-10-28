"use client"

import { type RefObject, useEffect } from "react"

import { PHONE_QUERY } from "@/constants/assistant"

/** While the panel (`root`, mounted only while it's open) is there, the wheel over it scrolls
 * only its messages (`scroller`, with overscroll-behavior: contain), never the page behind, even
 * where there's nothing to scroll; the page beside it scrolls as usual. On phones, where the panel is the whole screen, the page
 * doesn't scroll at all. Text fields in it scroll themselves. */
export function useContainedScroll(
  root: HTMLElement | null,
  scroller: RefObject<HTMLElement | null>
) {
  useEffect(() => {
    if (!root) {
      return
    }

    function onWheel(event: WheelEvent) {
      const target = event.target as Element
      const list = scroller.current

      if (target.closest("textarea")) {
        return
      }

      // Outside the messages, or with nothing in them to scroll, the page mustn't take it.
      if (!list?.contains(target) || list.scrollHeight <= list.clientHeight) {
        event.preventDefault()
      }
    }

    root.addEventListener("wheel", onWheel, { passive: false })
    const phone = window.matchMedia(PHONE_QUERY).matches
    const before = document.body.style.overflow

    if (phone) {
      document.body.style.overflow = "hidden"
    }

    return () => {
      root.removeEventListener("wheel", onWheel)

      if (phone) {
        document.body.style.overflow = before
      }
    }
  }, [root, scroller])
}
