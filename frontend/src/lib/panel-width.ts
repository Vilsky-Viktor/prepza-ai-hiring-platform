import { PANEL_WIDTH, SAVED_PANEL_WIDTH_KEY } from "@/constants/assistant"

/** The widest the panel may be in a window this wide. */
export function maxPanelWidth(windowWidth: number) {
  return Math.max(
    PANEL_WIDTH.min,
    Math.min(PANEL_WIDTH.max, Math.floor(windowWidth * PANEL_WIDTH.maxShare))
  )
}

/** `width` kept between the narrowest and the widest the panel may be. */
export function clampPanelWidth(width: number, windowWidth: number) {
  return Math.round(
    Math.min(Math.max(width, PANEL_WIDTH.min), maxPanelWidth(windowWidth))
  )
}

/** The width the user left the panel at, or the default. */
export function savedPanelWidth() {
  try {
    const saved = Number(localStorage.getItem(SAVED_PANEL_WIDTH_KEY))

    return saved > 0 ? saved : PANEL_WIDTH.default
  } catch {
    return PANEL_WIDTH.default
  }
}

export function savePanelWidth(width: number) {
  try {
    localStorage.setItem(SAVED_PANEL_WIDTH_KEY, String(width))
  } catch {
    // The width simply isn't remembered.
  }
}
