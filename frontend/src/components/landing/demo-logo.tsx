/** The pictures' made-up company logo, Acme's: two mountain peaks on an orange square with
 * rounded corners, like an uploaded logo. */
export function DemoLogo({ className }: { className: string }) {
  return (
    <svg viewBox="0 0 64 64" aria-hidden className={`shrink-0 ${className}`}>
      <rect width="64" height="64" rx="16" fill="#f97316" />
      <path d="M10 46 27 18l17 28Z" fill="#fff" />
      <path d="m32 46 11-17 11 17Z" fill="#fff" fillOpacity="0.7" />
    </svg>
  )
}
