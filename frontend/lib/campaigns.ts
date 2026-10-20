import type { Campaign } from "@/types/campaigns"

/** A campaign dialog's fields to start with: a new campaign's (an update, nothing written), or
 * `campaign`'s texts in `language`, its English ones while that language has none. */
export function campaignForm(campaign: Campaign | undefined, language: string) {
  const texts = campaign?.texts[language] ?? campaign?.texts.en

  return {
    kind: campaign?.kind ?? "updates",
    subject: texts?.subject ?? "",
    text: texts?.text ?? "",
    button: texts?.button ?? "",
    link: campaign?.link ?? "",
  }
}
