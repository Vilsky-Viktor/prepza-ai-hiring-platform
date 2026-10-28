"use client"

import { useTranslations } from "next-intl"

import { PANEL_WIDTH } from "@/constants/assistant"
import { clampPanelWidth, maxPanelWidth } from "@/lib/panel-width"

/** The handle on the panel's inner edge that sets its width: dragged, or with the arrow keys.
 * Wider screens only; `onResize` gets the width kept within the limits. */
export function PanelResizer({
  width,
  onResize,
}: {
  width: number
  onResize: (width: number) => void
}) {
  const t = useTranslations("assistant")

  // The panel is at the end side: in a right-to-left page, it's on the left.
  function rtl() {
    return document.documentElement.dir === "rtl"
  }

  function resize(next: number) {
    onResize(clampPanelWidth(next, window.innerWidth))
  }

  function onPointerDown(event: React.PointerEvent<HTMLDivElement>) {
    event.preventDefault()
    event.currentTarget.setPointerCapture(event.pointerId)
  }

  function onPointerMove(event: React.PointerEvent<HTMLDivElement>) {
    if (event.currentTarget.hasPointerCapture(event.pointerId)) {
      resize(rtl() ? event.clientX : window.innerWidth - event.clientX)
    }
  }

  function onKeyDown(event: React.KeyboardEvent<HTMLDivElement>) {
    const wider = rtl() ? "ArrowRight" : "ArrowLeft"
    const narrower = rtl() ? "ArrowLeft" : "ArrowRight"

    if (event.key === wider || event.key === narrower) {
      event.preventDefault()
      resize(width + (event.key === wider ? 1 : -1) * PANEL_WIDTH.step)
    }
  }

  return (
    <div
      role="separator"
      aria-orientation="vertical"
      aria-label={t("resize")}
      aria-valuenow={width}
      aria-valuemin={PANEL_WIDTH.min}
      aria-valuemax={
        typeof window === "undefined"
          ? PANEL_WIDTH.max
          : maxPanelWidth(window.innerWidth)
      }
      tabIndex={0}
      onPointerDown={onPointerDown}
      onPointerMove={onPointerMove}
      onKeyDown={onKeyDown}
      className="group absolute inset-y-0 -start-1.5 z-10 hidden w-3 cursor-col-resize touch-none rounded-full outline-none focus-visible:ring-3 focus-visible:ring-ring/50 sm:block"
    >
      <span
        aria-hidden
        className="absolute inset-y-0 start-1.5 w-px transition-all group-hover:w-0.5 group-hover:bg-foreground/30 group-active:w-0.5 group-active:bg-foreground/30 dark:group-hover:bg-foreground/20 dark:group-active:bg-foreground/20"
      />
    </div>
  )
}
