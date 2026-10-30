"use client"

import { cn } from "cn"
import { useTranslations } from "next-intl"

import { DemoDescription } from "@/features/landing/components/demo-description"
import { DemoFirstCompany } from "@/features/landing/components/demo-first-company"
import { DEMO_COMPANY, DEMO_DESCRIPTION } from "@/config/create-demo"
import { NAMING, PASTED, STEPS } from "@/config/create-demo-steps"
import { countedAt } from "@/hooks/use-demo-steps"

// The steps the paste menu is open for.
const MENU = ["menu", "aimPaste", "paste"]

/** The create demo's first screen at step `at`: the home page's start box (components/common/
 * start-test.tsx) in the middle, the description pasted into it and sent, then, in the same box,
 * the first company named. Both keep their place, so the box never changes size. */
export function CreateDescribe({ at }: { at: { index: number; n: number } }) {
  const start = useTranslations("start")
  const menu = useTranslations("landing.create.menu")
  const step = STEPS[at.index].name
  const naming = at.index >= NAMING

  return (
    <div className="flex flex-1 items-center justify-center">
      <div className="grid h-72 w-full max-w-176 rounded-xl bg-surface *:[grid-area:1/1]">
        <div className={cn("flex min-h-0", naming && "invisible")}>
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
        <div className={cn("flex min-h-0 p-4", !naming && "invisible")}>
          <DemoFirstCompany
            name={DEMO_COMPANY.slice(
              0,
              countedAt(STEPS, at, "naming", DEMO_COMPANY.length)
            )}
            typing={step === "focusName" || step === "naming"}
            pressed={step === "continue"}
          />
        </div>
      </div>
    </div>
  )
}
