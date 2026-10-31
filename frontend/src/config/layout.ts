// How far a page is scrolled (px) before the "back to top" button shows: about a screen.
export const SCROLL_TOP_AFTER_PX = 800

// The pages where questions run against the clock (an interview, a practice round, a company's
// preview), in any language: no header or footer there, only the questions.
export const TIMED_PAGE = /^(\/[a-z]{2,3})?\/sessions\//

// A company's invitation, shared test link and embedded interview, and a member's preview of its
// invitation: like its interview, they show the company only, without testee's header and footer.
export const COMPANY_INTERVIEW_PAGE =
  /^(\/[a-z]{2,3})?\/((invite|apply|embedded)\/|companies\/[^/]+\/interviews\/[^/]+\/try$)/

// How long a copy button shows its check mark after copying.
export const COPIED_MS = 3000
