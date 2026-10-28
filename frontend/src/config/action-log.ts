import type { ActionGroup } from "@/types/company"

// The action log's groups, in the filter's order (the API's AuditGroup).
export const ACTION_GROUPS = [
  "interviews",
  "candidates",
  "team",
  "company",
  "billing",
  "integrations",
] as const satisfies readonly ActionGroup[]

// The filters the action log's address carries.
export const ACTION_FILTERS = ["member_id", "group", "from", "to"] as const
