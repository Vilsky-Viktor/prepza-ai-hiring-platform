"use client"

import { useEffect, useState } from "react"

import { CompanyOptOuts } from "@/features/superadmin/components/company-opt-outs"
import { companyEmails } from "@/lib/superadmin-emails"
import type { CandidateOptOuts } from "@/types/superadmin"

/** The companies that invited the candidate's address, and the emails it stopped from each,
 * stopped or let through again here. Loaded in the browser: the address goes in a request's
 * body, never a page's address. */
export function CandidateEmailStops({ email }: { email: string }) {
  const [found, setFound] = useState<CandidateOptOuts>()

  useEffect(() => {
    companyEmails(email).then(setFound, () => undefined)
  }, [email])

  return found ? <CompanyOptOuts email={email} initial={found} /> : null
}
