// The AI chip (lucide's cpu-ai, 24 × 24, its 1.5 stroke) as an image, for a CSS mask: the loading
// mark shows its light only through the chip's lines.
const CHIP_LINES = [
  "M12 20v2",
  "M12 2v2",
  "M16 9v6",
  "M17 20v2",
  "M17 2v2",
  "M2 12h2",
  "M2 17h2",
  "M2 7h2",
  "M20 12h2",
  "M20 17h2",
  "M20 7h2",
  "M7 20v2",
  "M7 2v2",
  "M8 13h4",
  "M8 15v-4a2 2 0 014 0v4",
]

const CHIP_SVG =
  `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="black" ` +
  `stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">` +
  CHIP_LINES.map((d) => `<path d="${d}"/>`).join("") +
  `<rect x="4" y="4" width="16" height="16" rx="2"/></svg>`

export const AI_CHIP_MASK = `url("data:image/svg+xml,${encodeURIComponent(CHIP_SVG)}")`
