"use client"

import { useTranslations } from "next-intl"

import { InstructionsDialog } from "@/components/instructions-dialog"
import type { AtsProvider } from "@/constants/ats"

const STEPS = [
  "flowStage",
  "flowLink",
  "flowMove",
  "flowInvite",
  "flowFinish",
  "flowDecide",
] as const

/** An ATS's Instructions: how candidates come from the ATS and what goes back, step by step,
 * after any setup still to do there (`children`: a web hook to set up). */
export function CandidateFlow({
  provider,
  open,
  onOpenChange,
  children,
}: {
  provider: AtsProvider
  open: boolean
  onOpenChange: (open: boolean) => void
  children?: React.ReactNode
}) {
  const t = useTranslations("ats")

  return (
    <InstructionsDialog
      title={t("flowTitle", { ats: provider.name })}
      steps={STEPS.map((step) => t(step, { ats: provider.name }))}
      stepsTitle={t("flowHow")}
      open={open}
      onOpenChange={onOpenChange}
    >
      {children}
    </InstructionsDialog>
  )
}
