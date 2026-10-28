import type { components as accounts } from "@/types/api/accounts"
import type { components as billing } from "@/types/api/billing"
import type { components as companies } from "@/types/api/companies"
import type { components as generation } from "@/types/api/generation"
import type { components } from "@/types/api/library"
import type { components as notifications } from "@/types/api/notifications"

type Schemas = components["schemas"]

export type TemplateSummary = Schemas["TemplateSummary"]
export type Template = Schemas["TemplateOut"]
/** A template on its superadmin page: each topic's practice and company question counts. */
export type PooledTemplate = Schemas["PooledTemplateOut"]
export type TemplateFilters = Schemas["TemplateFiltersOut"]
export type FlaggedQuestion = Schemas["FlaggedQuestionOut"]
export type ReplacedQuestion = Schemas["ReplacedQuestionOut"]

/** A question on the quality tab: flagged now, or one revision of it as replaced. */
export type QualityRow = {
  // Replaced questions: the kept revision, whose reports are listed.
  revision_id?: string
  question_id: string
  text: string
  options: { answer: string; correct: boolean }[]
  flag?: string
  // A flagged template question: it can be fixed now or dismissed.
  actionable?: boolean
  answers: number
  correct: number
  reports: number
  set_title: string
  set_kind: string
  at: string
  // Replaced questions: what replaced this version.
  new_text?: string
  new_options?: { answer: string; correct: boolean }[]
}

/** A company interview's pass rate, for the monitoring tab. */
export type PassRate = companies["schemas"]["PassRateOut"]

/** A company sent for review, for the verification tab. */
export type VerificationRequest = companies["schemas"]["VerificationRequestOut"]

/** One service's counts in a month, for the stats tab. */
export type Stats = companies["schemas"]["StatsOut"]

/** A practice question of a template, with its answers, for the public role test pages. */
export type SampleQuestion = Schemas["SampleQuestionOut"]

/** The account an address signs in with, if any, for the emails tab. */
export type EmailLookup = accounts["schemas"]["EmailLookupOut"]

/** The companies that invited an address, and what it stopped, for the emails tab. */
export type CandidateOptOuts = notifications["schemas"]["CandidateOptOutsOut"]
// A company as the admin zone's companies tab lists it.
export type SuperadminCompany = companies["schemas"]["SuperadminCompanyOut"]
export type LegalNotice = notifications["schemas"]["LegalNoticeOut"]

/** What the support tab's search found: a company, an interview or a candidate, with its company. */
export type SupportResult = companies["schemas"]["SupportResultOut"]
/** A company as its support page shows it: badges, members and balance. */
export type SupportCompany = companies["schemas"]["SupportCompanyOut"]
/** An account on its support page: its companies and the top-ups it paid for. */
export type SupportUser = companies["schemas"]["SupportUserOut"]
/** A candidate on their support page: what happened, never their answers. */
export type SupportCandidate = companies["schemas"]["SupportCandidateOut"]
/** An interview on its support page, and one of its candidates there. */
export type SupportInterview = companies["schemas"]["SupportInterviewOut"]
export type SupportCandidateRow = companies["schemas"]["SupportCandidateRowOut"]

type Billing = billing["schemas"]

/** The AI costs tab: what AI cost in a period and why, and the limits' hits. */
export type AiCosts = Billing["AiCostsOut"]
export type LimitHitLists = Billing["LimitHitListsOut"]
export type LimitHits = Billing["LimitHitsOut"]
/** A shared daily budget's use today, from the service that owns it. */
export type Budget = generation["schemas"]["BudgetOut"]
/** A company's or user's AI spend lately, on its support page. */
export type AiSpend = Billing["AiSpendOut"]
/** Every limit, as the Controls tab edits them, and their changes. */
export type Limits = Billing["LimitsOut"]
export type Limit = Billing["LimitOut"]
export type LimitChange = Billing["LimitChangeOut"]
