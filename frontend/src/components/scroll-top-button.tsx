"use client"

import { ArrowUpIcon } from "lucide-react"
import { useTranslations } from "next-intl"
import { useEffect, useState } from "react"

import { Button } from "@/components/ui/button"
import { SCROLL_TOP_AFTER_PX } from "@/config/layout"

/** Back to the top of a long page, in its bottom end corner once it's scrolled down a screen.
 * Hidden on pages with their own bar at the bottom (topic review, an interview underway). */
export function ScrollTopButton() {
  const t = useTranslations("common")
  const [shown, setShown] = useState(false)

  useEffect(() => {
    function update() {
      setShown(window.scrollY > SCROLL_TOP_AFTER_PX)
    }

    update()
    window.addEventListener("scroll", update, { passive: true })

    return () => window.removeEventListener("scroll", update)
  }, [])

  if (!shown) {
    return null
  }

  return (
    <Button
      variant="outline"
      size="icon"
      aria-label={t("backToTop")}
      data-testid="back-to-top"
      // Smooth unless the visitor asked for less motion (the page's scroll-smooth).
      onClick={() => window.scrollTo({ top: 0 })}
      className="fixed end-6 bottom-6 z-30 size-12 rounded-xl bg-background [body:has([data-round-footer])_&]:hidden"
    >
      <ArrowUpIcon className="size-6" />
    </Button>
  )
}
