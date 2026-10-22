import type { Campaign, CampaignAudience } from "@/types/campaigns"

/** A campaign dialog's fields to start with: a new campaign's (an update to everyone, nothing
 * written), or `campaign`'s texts in `language`, its English ones while that language has none. */
export function campaignForm(campaign: Campaign | undefined, language: string) {
  const texts = campaign?.texts[language] ?? campaign?.texts.en

  return {
    kind: campaign?.kind ?? "updates",
    audience: audienceOf(campaign),
    subject: texts?.subject ?? "",
    text: texts?.text ?? "",
    button: texts?.button ?? "",
    link: campaign?.link ?? "",
  }
}

/** Whom `campaign` goes to, as its dialog shows it; everyone for a new one. */
function audienceOf(campaign: Campaign | undefined): CampaignAudience {
  if (!campaign) {
    return { groups: [], editorsOnly: false, companies: [] }
  }

  return {
    groups: campaign.groups,
    editorsOnly: campaign.editors_only,
    companies: campaign.companies,
  }
}
