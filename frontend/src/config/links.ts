// A link inside running text. Never underlined (the site's design); told apart from the text
// around it without relying on color by its weight (WCAG 1.4.1), in the foreground color: 3.3:1
// against the muted body text in light, and at least 4.5:1 against the page in both themes. On
// hover it takes the primary color; on focus, the site's focus ring.
export const TEXT_LINK =
  "rounded-sm font-medium text-foreground transition-colors outline-none hover:text-primary focus-visible:ring-3 focus-visible:ring-ring/50"
