/** The pictures' made-up company logo, Acme's: its two mountain peaks over its name in white on an
 * orange square with rounded corners, like an uploaded logo. */
export function DemoLogo({ className }: { className: string }) {
  return (
    <svg viewBox="0 0 64 64" aria-hidden className={`shrink-0 ${className}`}>
      <rect width="64" height="64" rx="16" fill="#f97316" />
      <path d="M17 33 27 15l10 18Z" fill="#fff" />
      <path d="m30 33 7-11 7 11Z" fill="#fff" fillOpacity="0.7" />
      <text
        x="32"
        y="48"
        textAnchor="middle"
        fill="#fff"
        fontSize="14"
        fontWeight="600"
        letterSpacing="0.5"
        style={{ fontFamily: "var(--font-poppins), sans-serif" }}
      >
        ACME
      </text>
    </svg>
  )
}
