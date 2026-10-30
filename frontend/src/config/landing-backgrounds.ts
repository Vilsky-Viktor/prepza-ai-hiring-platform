// The landing sections' backgrounds, each drawn by a ::before under its element's content and
// as wide as the window, while the content keeps the page's width.

// The window-wide layer itself: the page's whole width, edge to edge (its element is centred in
// the page's container, app/page.tsx). Not over a scrollbar's gutter: anything there would let
// the page scroll sideways.
const LAYER =
  "relative before:pointer-events-none before:absolute before:start-[calc(50%-50cqw)] before:-z-10 before:w-[100cqw]"

// A grey band: the site's one grey, top to bottom of its element.
export const BAND = `${LAYER} before:inset-y-0 before:bg-surface`

// A faint dot grid in the borders' colour, 24 px apart, across the window, fading out only at its
// top and bottom.
export const DOT_GRID = `${LAYER} before:inset-y-0 before:bg-[radial-gradient(var(--border)_1.5px,transparent_1.5px)] before:bg-size-[24px_24px] before:mask-[linear-gradient(to_bottom,transparent,black_15%,black_85%,transparent)]`

// A soft glow of the primary colour in an ellipse as large as its element, no edges, the same
// strength in both themes.
export const GLOW = `${LAYER} before:inset-y-0 before:bg-[radial-gradient(ellipse_closest-side,color-mix(in_oklch,var(--primary)_16%,transparent),transparent)] dark:before:bg-[radial-gradient(ellipse_closest-side,color-mix(in_oklch,var(--primary)_16%,transparent),transparent)]`

// A card the section's background shows through faintly: the site's grey at 75%, no blur (the
// interview card among the ways in).
export const SEE_THROUGH_CARD =
  "bg-[color-mix(in_oklab,var(--muted)_75%,transparent)] dark:bg-[color-mix(in_oklab,color-mix(in_oklab,var(--muted)_40%,var(--background))_75%,transparent)]"

// A grey card the glow shows through a little, in light only (the dark grey is see-through
// already): the Mira section's chat and cards.
export const GLOW_CARD =
  "bg-[color-mix(in_oklab,var(--muted)_70%,transparent)] dark:bg-surface"
