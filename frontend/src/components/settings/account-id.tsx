"use client"

import { useAuth } from "@/components/auth-provider"
import { EntityId } from "@/components/entity-id"

/** The signed-in account's id, to quote when writing to prepza about the account. */
export function AccountId() {
  const { user } = useAuth()

  return user ? <EntityId id={user.uid} form="button" /> : null
}
