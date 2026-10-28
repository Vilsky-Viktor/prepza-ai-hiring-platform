// The roles the owner gives a company member, as the API takes them; the first is the default.
export const MEMBER_ROLES = ["admin", "viewer"] as const

export type MemberRole = (typeof MEMBER_ROLES)[number]
