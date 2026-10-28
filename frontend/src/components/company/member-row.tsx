"use client"

import { useTranslations } from "next-intl"
import { useState } from "react"
import { toast } from "sonner"

import { MakeOwner } from "@/components/company/make-owner"
import { RemoveMember } from "@/components/company/remove-member"
import { RolePicker } from "@/components/company/role-picker"
import { CopyField } from "@/components/common/copy-field"
import { Badge } from "@/components/ui/badge"
import { WrappedEmail } from "@/components/common/wrapped-email"
import type { MemberRole } from "@/config/roles"
import { apiErrorMessage, apiFetch } from "@/lib/api"
import { hasMessage } from "@/lib/messages"
import type { CompanyMember } from "@/types/company"

export function MemberRow({
  companyId,
  member,
  onRemoved,
}: {
  companyId: string
  member: CompanyMember
  onRemoved: () => void
}) {
  const t = useTranslations("members")
  const roles = useTranslations("roles")
  const [role, setRole] = useState(member.role)
  const [saving, setSaving] = useState(false)
  const [makingOwner, setMakingOwner] = useState(false)

  // The owner changes an admin to a viewer or back; the row shows the new role once saved.
  async function changeRole(next: MemberRole) {
    if (next === role) {
      return
    }

    setSaving(true)

    try {
      await apiFetch(
        `/companies/members/${member.id}/role?company_id=${companyId}`,
        { method: "PUT", body: JSON.stringify({ role: next }) }
      )
      setRole(next)
    } catch (error) {
      toast.error(apiErrorMessage(error, t("roleFailed")))
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="space-y-3 p-6">
      {/* On phones the role, or choosing it and removing the member, take their own line under
          the email. */}
      <div className="flex items-center justify-between gap-4 max-sm:flex-wrap max-sm:gap-3">
        <span className="min-w-0 max-sm:basis-full">
          <span className="block text-lg font-medium">
            <WrappedEmail email={member.email} />
          </span>
          <span className="text-sm text-muted-foreground">
            {member.joined ? t("joined") : t("invited")}
          </span>
        </span>
        <span className="flex items-center gap-2 max-sm:basis-full">
          {/* The owner manages every row but their own: its role and removing it. */}
          {member.removable ? (
            <RolePicker
              role={role as MemberRole}
              onChange={changeRole}
              disabled={saving}
              className="w-44"
              // Choosing "owner" asks to confirm handing the company over first.
              onMakeOwner={
                member.can_own ? () => setMakingOwner(true) : undefined
              }
            />
          ) : (
            <Badge variant="secondary" className="h-7 px-3 text-sm font-light">
              {hasMessage(roles, role) ? roles(role) : role}
            </Badge>
          )}
          {member.removable && (
            <RemoveMember
              companyId={companyId}
              member={member}
              onRemoved={onRemoved}
            />
          )}
        </span>
      </div>
      {member.can_own && (
        <MakeOwner
          companyId={companyId}
          member={member}
          open={makingOwner}
          onOpenChange={setMakingOwner}
        />
      )}
      {/* The join link in the site's copy field, like the test's shareable link. */}
      {!member.joined && member.token && (
        <CopyField path={`/join/${member.token}`} />
      )}
    </div>
  )
}
