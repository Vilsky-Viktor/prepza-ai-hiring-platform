import type { components } from "@/types/api/library"

type Schemas = components["schemas"]

export type EmailPreferences = Schemas["EmailPreferencesOut"]
export type EmailSetting = keyof EmailPreferences
export type EmailChanges = Partial<EmailPreferences>
export type EmailSource = Schemas["EmailPreferencesIn"]["source"]
