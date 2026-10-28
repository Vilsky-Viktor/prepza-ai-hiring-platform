"use client"

import { useTranslations } from "next-intl"

import { SortMenu } from "@/components/common/sort-menu"
import { CANDIDATE_SORTS, type CandidateSort } from "@/config/interviews"

/** Chooses how the candidates are listed (components/common/sort-menu.tsx). */
export function CandidateSortMenu({ current }: { current: CandidateSort }) {
  const t = useTranslations("candidates")

  return (
    <SortMenu
      current={current}
      label={t("sortBy", { sort: t(`sort.${current}`) })}
      options={CANDIDATE_SORTS.map((sort) => ({
        value: sort,
        label: t(`sort.${sort}`),
      }))}
    />
  )
}
