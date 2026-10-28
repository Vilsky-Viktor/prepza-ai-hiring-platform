import { UploadIcon, UserIcon, UsersIcon } from "lucide-react"

import type { InviteTab } from "@/constants/invites"

// The invite dialog's tab icons: one candidate, many, a file.
export const INVITE_TAB_ICONS = {
  one: UserIcon,
  many: UsersIcon,
  file: UploadIcon,
} satisfies Record<InviteTab, unknown>
