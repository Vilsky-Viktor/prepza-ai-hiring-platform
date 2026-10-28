import type { components } from "@/types/api/notifications"

type Schemas = components["schemas"]

export type Campaign = Schemas["CampaignOut"]
export type CampaignRow = Schemas["CampaignRowOut"]
export type CampaignTexts = Schemas["CampaignTexts"]
export type CampaignPreview = Schemas["PreviewOut"]
export type CampaignKind = Schemas["AudienceIn"]["kind"]
export type AudienceGroup = Schemas["AudienceGroup"]
export type CampaignCompany = Schemas["CompanyOut"]
/** Whom a campaign goes to, as its dialog chooses it: everyone (no groups) or some groups, of
 * companies their owners and admins only, and for an important notice some companies only. */
export type CampaignAudience = {
  groups: AudienceGroup[]
  editorsOnly: boolean
  companies: CampaignCompany[]
}
export type LegalChange = Schemas["LegalChangeOut"]
