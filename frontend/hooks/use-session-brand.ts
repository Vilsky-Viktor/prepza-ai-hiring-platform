"use client"

import { useEffect, useState } from "react"

import { useBrandColors } from "@/hooks/use-brand-colors"
import { apiFetch } from "@/lib/api"
import type { Brand, Company } from "@/types/company"

/** Who a test is for, for its logo and colors (over the page while it's open). A member's
 * preview comes from its test's page (/companies/{id}/..., `testHref`), so its company is
 * known; a preview has no invite behind it. A practice round has no company. Without it, the
 * test goes on as before. */
export function useSessionBrand(
  testHref: string | undefined,
  inviteId: string | null | undefined,
  practice: boolean
): Brand | null {
  const [brand, setBrand] = useState<Brand | null>(null)
  useBrandColors(brand?.brand_colors, brand?.theme, brand?.brand_style)
  const previewCompany = testHref?.split("/")[2]

  useEffect(() => {
    const brandOf = previewCompany
      ? apiFetch<Company>(`/companies/companies/${previewCompany}`).then(
          (company) => ({
            company: company.name,
            logo_url: company.logo_url ?? null,
            brand_colors: company.candidate_colors ?? null,
            brand_style: company.brand_style ?? null,
          })
        )
      : inviteId && !practice
        ? apiFetch<Brand>(`/companies/candidates/${inviteId}/brand`)
        : null

    brandOf?.then(setBrand).catch(() => setBrand(null))
  }, [inviteId, previewCompany, practice])

  return brand
}
