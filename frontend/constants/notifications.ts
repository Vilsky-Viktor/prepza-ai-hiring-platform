import {
  BadgeCheckIcon,
  BadgeXIcon,
  CrownIcon,
  DollarSignIcon,
  FlagIcon,
  MailWarningIcon,
  PencilOffIcon,
  NewspaperIcon,
  PackageCheckIcon,
  ScaleIcon,
  SparklesIcon,
  UnplugIcon,
  UserCheckIcon,
  UserPlusIcon,
  UserXIcon,
  XCircleIcon,
  type LucideIcon,
} from "lucide-react"

// The badge shows the unread count up to this, then "9+".
export const MAX_BADGE_COUNT = 9
// After a dropped live stream, wait this long before reconnecting, doubling up to the maximum.
export const RECONNECT_MS = 2000
export const MAX_RECONNECT_MS = 60000

// How each kind the services send (prepza_common.notifications.NotificationKind) looks: its
// icon, and whether it's a problem to act on (shown in red).
export const NOTIFICATION_LOOKS: Record<
  string,
  { icon: LucideIcon; alert: boolean }
> = {
  question_flagged: { icon: FlagIcon, alert: false },
  question_fixed: { icon: SparklesIcon, alert: false },
  referral_rewarded: { icon: DollarSignIcon, alert: false },
  auto_top_up_charged: { icon: DollarSignIcon, alert: false },
  auto_top_up_failed: { icon: DollarSignIcon, alert: true },
  candidate_finished: { icon: UserCheckIcon, alert: false },
  invite_undelivered: { icon: MailWarningIcon, alert: true },
  interview_ready: { icon: PackageCheckIcon, alert: false },
  interview_cancelled: { icon: XCircleIcon, alert: true },
  verification_approved: { icon: BadgeCheckIcon, alert: false },
  verification_declined: { icon: BadgeXIcon, alert: true },
  ats_not_invited: { icon: UserXIcon, alert: true },
  ats_cannot_write: { icon: PencilOffIcon, alert: true },
  connection_broken: { icon: UnplugIcon, alert: true },
  webhook_stopped: { icon: UnplugIcon, alert: true },
  member_joined: { icon: UserPlusIcon, alert: false },
  ownership_received: { icon: CrownIcon, alert: false },
  news: { icon: NewspaperIcon, alert: false },
  legal_terms: { icon: ScaleIcon, alert: false },
  legal_privacy: { icon: ScaleIcon, alert: false },
  legal_dpa: { icon: ScaleIcon, alert: false },
}
// Sent on the window when the user joins a company: the bell reconnects with their companies
// read again, so it hears the new one at once.
export const COMPANIES_CHANGED = "prepza:companies-changed"
// A closed legal banner stays closed in this browser, for that document's version.
export const LEGAL_BANNER_KEY = "prepza:legal-banner:{document}:{version}"

/** A notification's message values the service left out. "none" is what the messages'
 * selects read as "leave it out"; `role` is a member's ("admin" or "viewer"); `ats` is the ATS
 * a candidate came from, which older notifications don't name; `integration` is what stopped
 * working ("slack", or an ATS); `url` is a web hook's address. */
export const NOTIFICATION_DEFAULTS = {
  title: "none",
  topic: "",
  grade: "none",
  name: "",
  domain: "",
  reason: "none",
  role: "",
  ats: "ATS",
  integration: "ats",
  url: "",
}
