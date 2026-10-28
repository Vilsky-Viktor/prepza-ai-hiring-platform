// The services that own a shared daily budget (each answers GET /superadmin/budgets), by their
// API path: generation's daily generations and quality checks, the assistant's tokens and the
// help chat's.
export const BUDGET_SOURCES = ["generate", "assistant"] as const
