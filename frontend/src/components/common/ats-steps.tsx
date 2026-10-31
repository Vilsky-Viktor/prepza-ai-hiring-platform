"use client"

import { ArrowRightIcon } from "lucide-react"
import { useTranslations } from "next-intl"

import {
  BREEZY_KEY_PATH,
  GREENHOUSE_CREDENTIAL_PATH,
  GREENHOUSE_CREDENTIAL_TYPE,
  GREENHOUSE_PERMISSIONS,
  RECRUITEE_TOKEN_PATH,
  TEAMTAILOR_KEY_ACCESS,
  TEAMTAILOR_KEY_PATH,
  WORKABLE_SCOPES,
  WORKABLE_TOKEN_PATH,
} from "@/config/ats"

/** An ATS's own words (menus, scopes, events), in chips like code in questions. */
export function Chips({ items, path }: { items: string[]; path?: boolean }) {
  return (
    <span className="flex flex-wrap items-center gap-1.5">
      {items.map((item, index) => (
        <span key={item} className="flex items-center gap-1.5">
          {path && index > 0 && (
            <ArrowRightIcon aria-hidden className="size-4 rtl:rotate-180" />
          )}
          <span className="rounded bg-surface px-1.5 py-0.5 font-mono text-sm text-foreground">
            {item}
          </span>
        </span>
      ))}
    </span>
  )
}

/** Where to make the token in Workable, step by step. */
export function WorkableSteps() {
  const t = useTranslations("ats")

  return (
    <ol className="list-decimal space-y-3 ps-5 text-base text-muted-foreground">
      <li className="space-y-1.5">
        <span className="block">{t("stepOpen", { ats: "Workable" })}</span>
        <Chips items={WORKABLE_TOKEN_PATH} path />
      </li>
      <li className="space-y-1.5">
        <span className="block">{t("stepScopes")}</span>
        <Chips items={WORKABLE_SCOPES} />
      </li>
      <li>{t("stepPaste", { ats: "Workable" })}</li>
    </ol>
  )
}

/** Where to make the API credential in Greenhouse, step by step. */
export function GreenhouseSteps() {
  const t = useTranslations("ats")

  return (
    <ol className="list-decimal space-y-3 ps-5 text-base text-muted-foreground">
      <li className="space-y-1.5">
        <span className="block">{t("stepOpen", { ats: "Greenhouse" })}</span>
        <Chips items={GREENHOUSE_CREDENTIAL_PATH} path />
      </li>
      <li className="space-y-1.5">
        <span className="block">{t("ghStepCreate")}</span>
        <Chips items={[GREENHOUSE_CREDENTIAL_TYPE]} />
      </li>
      <li className="space-y-1.5">
        <span className="block">{t("ghStepPermissions")}</span>
        <Chips items={GREENHOUSE_PERMISSIONS} />
      </li>
      <li>{t("ghStepPaste")}</li>
    </ol>
  )
}

/** Where to make the API key in Teamtailor, step by step. */
export function TeamtailorSteps() {
  const t = useTranslations("ats")

  return (
    <ol className="list-decimal space-y-3 ps-5 text-base text-muted-foreground">
      <li className="space-y-1.5">
        <span className="block">{t("stepOpen", { ats: "Teamtailor" })}</span>
        <Chips items={TEAMTAILOR_KEY_PATH} path />
      </li>
      <li className="space-y-1.5">
        <span className="block">{t("ttStepCreate")}</span>
        <Chips items={TEAMTAILOR_KEY_ACCESS} />
      </li>
      <li>{t("ttStepPaste")}</li>
    </ol>
  )
}

/** Where to make the personal API token in Recruitee, step by step. */
export function RecruiteeSteps() {
  const t = useTranslations("ats")

  return (
    <ol className="list-decimal space-y-3 ps-5 text-base text-muted-foreground">
      <li className="space-y-1.5">
        <span className="block">{t("stepOpen", { ats: "Recruitee" })}</span>
        <Chips items={RECRUITEE_TOKEN_PATH} path />
      </li>
      <li>{t("rcStepCreate")}</li>
      <li>{t("stepPaste", { ats: "Recruitee" })}</li>
    </ol>
  )
}

/** Where to make the API key in Breezy HR, step by step; testee adds the web hook itself. */
export function BreezySteps() {
  const t = useTranslations("ats")

  return (
    <ol className="list-decimal space-y-3 ps-5 text-base text-muted-foreground">
      <li className="space-y-1.5">
        <span className="block">{t("bzStepOpen")}</span>
        <Chips items={BREEZY_KEY_PATH} path />
      </li>
      <li>{t("bzStepCreate")}</li>
      <li>{t("bzStepPaste")}</li>
    </ol>
  )
}
