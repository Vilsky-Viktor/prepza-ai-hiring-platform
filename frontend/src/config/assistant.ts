import type { MessageKey } from "@/types/messages"

// The in-app assistant's panel.

// The welcome's questions by the user's stage (the assistant's GET /welcome decides it;
// signed-out visitors are "signed_out"), by their key in "assistant.welcome.<stage>.questions".
export const WELCOME_QUESTIONS: Record<string, string[]> = {
  signed_out: ["what", "pricing", "takeTest", "account"],
  no_company: ["firstInterview", "createCompany", "verify"],
  unverified: ["verify", "whyVerify", "createInterview"],
  no_interviews: ["fromDescription", "template", "changeQuestions"],
  no_candidates: ["invite", "shareLink", "ats"],
  has_candidates: ["passed", "compare", "replace", "signals"],
}

// The pages an answer links to, by their path, and the "assistant.pages" message naming each;
// the first match wins. Links come from the service, built from each tool's page.
export const LINK_PAGES: [RegExp, MessageKey<"assistant.pages">][] = [
  [/^\/pricing$/, "pricing"],
  [/^\/top-up$/, "topUp"],
  [/^\/settings$/, "settings"],
  [/^\/faq$/, "faq"],
  [/^\/companies$/, "companies"],
  [/^\/generate\//, "topics"],
  [/^\/sessions\//, "practice"],
  [/^\/news$/, "news"],
  [/\/integrations\/slack$/, "slack"],
  [/\/integrations\/api$/, "api"],
  [/\/integrations(\/[^/]+)?$/, "integrations"],
  [/\/templates\/[^/]+$/, "template"],
  [/\/templates$/, "templates"],
  [/\/members$/, "team"],
  [/\/referrals$/, "referrals"],
  [/\/candidates\/[^/]+$/, "candidate"],
  [/\/candidates$/, "candidates"],
  [/\/interviews\/[^/]+$/, "interview"],
  [/\/interviews$/, "interviews"],
]

// The service's link pages (its `show` tool) and the "assistant.pages" message naming each.
export const PAGE_LABELS: Record<string, MessageKey<"assistant.pages">> = {
  interview: "interview",
  interview_candidates: "candidates",
  candidate: "candidate",
  company: "interviews",
  members: "team",
  templates: "templates",
  template: "template",
  integrations: "integrations",
  ats: "integrations",
  slack: "slack",
  api: "api",
  referrals: "referrals",
  top_up: "topUp",
  pricing: "pricing",
  settings: "settings",
  faq: "faq",
  contact: "contact",
  news: "news",
}

// A company's pages: /companies/<id>/…, maybe under a language's prefix.
export const COMPANY_PATH =
  /^(?:\/[a-z]{2,3})?\/companies\/([0-9a-f-]{36})(?:\/|$)/

// The panel is the whole screen below this width, where a link it opens closes it.
export const PHONE_QUERY = "(max-width: 639px)"
// A touch screen, where focusing the input would pop the keyboard over the panel.
export const TOUCH_QUERY = "(pointer: coarse)"

// Voice messages: the formats to record in, the first the browser can (Chrome and Firefox take
// the first, Safari the second); a press shorter than this isn't sent; sliding the pointer
// this far from the button while holding it cancels.
export const RECORDING_TYPES = ["audio/webm;codecs=opus", "audio/mp4"]
export const MIN_RECORDING_MS = 500
export const CANCEL_DISTANCE_PX = 40

// What the panel keeps across reloads, per browser: signed in, whether it was open and the
// conversation it showed (localStorage; conversations themselves are on the server); signed
// out, whether it was open and the visitor's messages (sessionStorage, this tab only).
export const SAVED_CHAT_KEY = "prepza:assistant"
export const SAVED_VISITOR_CHAT_KEY = "prepza:assistant:visitor"

// The panel's width on wider screens, which the user drags: the default (28rem), the narrowest,
// and the widest (900px, or 70% of the window when that's less); a key press moves it this far.
// Kept per browser.
export const PANEL_WIDTH = {
  default: 448,
  min: 360,
  max: 900,
  maxShare: 0.7,
  step: 16,
}
export const SAVED_PANEL_WIDTH_KEY = "prepza:assistant:width"
