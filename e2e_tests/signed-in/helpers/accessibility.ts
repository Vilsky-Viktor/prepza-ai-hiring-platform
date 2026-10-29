import AxeBuilder from "@axe-core/playwright"
import { expect, type Page } from "@playwright/test"

// WCAG 2.0 A and AA, the rules axe checks for them.
const WCAG_AA = ["wcag2a", "wcag2aa"]

// Known issues: found by the scan, tracked here until fixed, rather than turning their rules off.
// Each names the rule, the element (a part of its HTML) and why it waits.
const KNOWN_ISSUES: { rule: string; html: RegExp; why: string }[] = []

/** The page as it is now (an open dialog included) checked with axe against WCAG 2.0 A and AA;
 * `name` says which screen, for the failure's message. */
export async function expectAccessible(page: Page, name: string) {
  const results = await new AxeBuilder({ page }).withTags(WCAG_AA).analyze()
  const found = results.violations.flatMap((violation) =>
    violation.nodes
      .filter(
        (node) =>
          !KNOWN_ISSUES.some((known) => known.rule === violation.id && known.html.test(node.html))
      )
      // The element itself, as its id alone (Base UI's are generated) says nothing.
      .map((node) => `${violation.id}: ${node.html.slice(0, 200)}: ${node.failureSummary}`)
  )

  expect(found, name).toEqual([])
}
