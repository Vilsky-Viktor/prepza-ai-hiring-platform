// Every card's padding, the same on every screen: a bordered card's (CARD) and a sign card's top,
// end and bottom.
export const CARD_PADDING = "p-6"

// A bordered card.
export const CARD = `rounded-xl border ${CARD_PADDING}`

// A card with a CornerSign (components/corner-sign.tsx): the soft grey of the side menu's active
// item, clipping the sign at its corner, with room on its start side for it.
export const SIGN_CARD = `relative overflow-hidden rounded-xl bg-muted/50 ${CARD_PADDING} ps-20`
