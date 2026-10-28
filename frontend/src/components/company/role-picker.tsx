"use client"

import { useTranslations } from "next-intl"

import { MenuPill } from "@/components/menu-pill"
import { MEMBER_ROLES, type MemberRole } from "@/config/roles"

/** A member's role, admin or viewer: the site's select pill opening a menu with a line on what
 * each role allows. With `onMakeOwner` (a member the API says can own the company), "owner"
 * too, which calls it instead of `onChange`. */
export function RolePicker({
  role,
  onChange,
  disabled,
  className,
  onMakeOwner,
}: {
  role: MemberRole
  onChange: (role: MemberRole) => void
  disabled?: boolean
  className?: string
  onMakeOwner?: () => void
}) {
  const t = useTranslations("roles")
  const members = useTranslations("members")

  return (
    <MenuPill
      ariaLabel={members("role")}
      value={role}
      options={[
        ...MEMBER_ROLES,
        ...(onMakeOwner ? ["owner" as const] : []),
      ].map((option) => ({
        value: option,
        label: t(option),
        note: t(`${option}Note`),
      }))}
      onChange={(value) =>
        value === "owner" ? onMakeOwner?.() : onChange(value as MemberRole)
      }
      disabled={disabled}
      className={className}
    />
  )
}
