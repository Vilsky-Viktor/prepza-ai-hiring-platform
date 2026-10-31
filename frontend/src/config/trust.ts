// The trust page's lists, by their message keys ("trust.<section>.<key>"), in the order shown.
export const TRUST_SECURITY = [
  "signIn",
  "encryption",
  "access",
  "limits",
  "logs",
  "actionLog",
  "backups",
  "breaches",
] as const
export const TRUST_PRIVACY = [
  "roles",
  "noSelling",
  "noInference",
  "voice",
  "ai",
  "rights",
] as const
export const TRUST_COMPLIANCE = [
  "aiAct",
  "humanReview",
  "dpa",
  "documents",
  "nyc",
] as const
export const TRUST_RETENTION = [
  "account",
  "results",
  "actionLog",
  "chats",
  "aiRecords",
  "errors",
  "backups",
  "statistics",
  "purchases",
] as const

// The legal pages and the compliance documents, linked at the end, by their message keys
// ("trust.links.<key>").
export const TRUST_LINKS = [
  { href: "/terms", key: "terms" },
  { href: "/privacy", key: "privacy" },
  { href: "/dpa", key: "dpa" },
  { href: "/documents", key: "documents" },
] as const

// The day the EU AI Act's duties for high-risk systems, testee among them, apply, and the day
// testee's own independent bias audit is done by (content/documents/instructions-for-companies.md).
export const AI_ACT_APPLIES = "2027-12-02"

// The data processing agreement's list of sub-processors, which the page shows as the site
// service serves it: the section with this heading in the binding English text.
export const SUBPROCESSORS_HEADING = "Sub-processors"
