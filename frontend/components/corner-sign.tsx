/** A card's sign, large and half transparent on its start edge, centred vertically and running
 * under the start border, the same size on a card of any height (a short card also clips its top
 * and bottom). The card is `SIGN_CARD` (constants/cards.ts): it clips the sign and leaves room for
 * it. */
export function CornerSign({ children }: { children: React.ReactNode }) {
  return (
    <span
      aria-hidden
      data-testid="corner-sign"
      className="absolute -start-5 top-1/2 flex -translate-y-1/2 opacity-50 [&_svg]:size-20"
    >
      {children}
    </span>
  )
}
