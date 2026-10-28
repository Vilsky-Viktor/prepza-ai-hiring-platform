import type { REPORT_REASONS } from "@/constants/feedback"
import type { components } from "@/types/api/library"

type Schemas = components["schemas"]

export type ReportReason = (typeof REPORT_REASONS)[number]
export type QuestionReport = Schemas["ReportOut"]
export type QuestionStats = Schemas["QuestionText"]
