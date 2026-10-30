"use client"

import { useTranslations } from "next-intl"

import { DemoDescription } from "@/features/landing/components/demo-description"
import { DemoFirstCompany } from "@/features/landing/components/demo-first-company"
import { DEMO_COMPANY, DEMO_DESCRIPTION } from "@/config/create-demo"
import { NAMING, PASTED, STEPS, TOPICS } from "@/config/create-demo-steps"
import { countedAt } from "@/hooks/use-demo-steps"

// The steps the paste menu is open for.
const MENU = ["menu", "aimPaste", "paste"]

/** The create demo's first screen at step `at`: the home page's start box (components/common/
 * start-test.tsx) in the middle, the description pasted into it and sent; then the window that
 * asks for a first company over it, the name typed and continued. The box keeps its place and
 * size throughout. */
export function CreateDescribe({ at }: { at: { index: number; n: number } }) {
  const start = useTranslations("start")
  const menu = useTranslations("landing.create.menu")
  const step = STEPS[at.index].name

  return (
    <div className="flex flex-1 items-center justify-center">
      <div className="flex h-72 w-full max-w-176 rounded-xl bg-surface">
        <DemoDescription
          text={DEMO_DESCRIPTION}
          pasted={at.index >= PASTED}
          menu={MENU.includes(step)}
          pasting={step === "paste"}
          pressed={step === "send"}
          placeholder={start("placeholder")}
          labels={{
            cut: menu("cut"),
            copy: menu("copy"),
            paste: menu("paste"),
          }}
        />
      </div>
      <DemoFirstCompany
        open={at.index >= NAMING && at.index < TOPICS}
        name={DEMO_COMPANY.slice(
          0,
          countedAt(STEPS, at, "naming", DEMO_COMPANY.length)
        )}
        typing={step === "focusName" || step === "naming"}
        pressed={step === "continue"}
      />
    </div>
  )
}
