/** A company's logo as uploaded, scaled to fit `className`'s box; candidates see it on their
 * pages and reports. A plain image: logos come from the API, already small. */
export function CompanyLogo({
  url,
  name,
  className,
}: {
  url: string
  name: string
  className?: string
}) {
  // eslint-disable-next-line @next/next/no-img-element
  return <img src={url} alt={name} className={className} />
}
