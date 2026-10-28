import { apiFetch } from "@/lib/api"
import type {
  EmailChanges,
  EmailPreferences,
  EmailSource,
} from "@/types/emails"

/** Saves some email settings; the API answers with all of them. */
export function saveEmailPreferences(
  changes: EmailChanges,
  source: EmailSource
) {
  return apiFetch<EmailPreferences>("/library/me/email-preferences", {
    method: "PUT",
    body: JSON.stringify({ changes, source }),
  })
}

/** What a sign-in sends: product updates on unless the person ticked the opt-out (the API turns
 * them on only at a first sign-in), and promotions only when ticked, since an unticked box must
 * not turn off what a returning user agreed to before. */
export function signInEmailChanges(choices: {
  noUpdates: boolean
  promotions: boolean
}): EmailChanges {
  return {
    updates: !choices.noUpdates,
    ...(choices.promotions ? { promotions: true } : {}),
  }
}
