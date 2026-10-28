// `exact`: current only on that page itself.
export const NAV_LINKS = [
  {
    href: "/companies",
    label: "hiring",
    signedInOnly: false,
    exact: false,
  },
  {
    href: "/pricing",
    label: "pricingLink",
    signedInOnly: false,
    exact: false,
  },
] as const

// The footer's links in three columns: the product, resources to read, and the company;
// `label` is the nav message.
export const FOOTER_COLUMNS = [
  [
    { href: "/tests", label: "tests" },
    { href: "/pre-employment-testing", label: "preEmploymentTesting" },
    { href: "/ai-interviews", label: "aiInterviews" },
    { href: "/practice", label: "practice" },
    { href: "/compare", label: "compare" },
  ],
  [
    { href: "/guides", label: "guides" },
    { href: "/faq", label: "faq" },
    { href: "/documents", label: "docs" },
    { href: "/api-docs", label: "apiDocs" },
    { href: "/news", label: "news" },
  ],
  [
    { href: "/about", label: "about" },
    { href: "/contact", label: "contact" },
    { href: "/privacy", label: "privacy" },
    { href: "/terms", label: "terms" },
    { href: "/accessibility", label: "accessibility" },
  ],
] as const
