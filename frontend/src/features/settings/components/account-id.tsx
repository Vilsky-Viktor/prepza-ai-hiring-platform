"use client"

import { useAuth } from "@/providers/auth-provider"
import { EntityId } from "@/components/common/entity-id"

/** The signed-in account's id, to quote when writing to testee about the account. */
export function AccountId() {
  const { user } = useAuth()

  return user ? <EntityId id={user.uid} form="button" /> : null
}
