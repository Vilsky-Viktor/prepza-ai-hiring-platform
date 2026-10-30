"use client"

import { cn } from "cn"
import { useTranslations } from "next-intl"
import { useState } from "react"

import { DemoClickSession } from "@/features/landing/components/demo-click-session"
import { DemoInvitation } from "@/features/landing/components/demo-invitation"
import { DemoMicPrompt } from "@/features/landing/components/demo-mic-prompt"
import { DemoPanel } from "@/features/landing/components/demo-panel"
import { DemoPointer } from "@/features/landing/components/demo-pointer"
import { DemoStartAction } from "@/features/landing/components/demo-start-action"
import { DemoVoiceSession } from "@/features/landing/components/demo-voice-session"
import { AnswerModeSwitch } from "@/features/company/components/answer-mode-switch"
import { CLICK_QUESTIONS, DEMO_SAID } from "@/config/candidates-demo"
import {
  CLICK_START,
  STEPS,
  TARGETS,
  VOICE_START,
} from "@/config/candidates-demo-steps"
import { pointedAt, stepIndex, useDemoSteps } from "@/hooks/use-demo-steps"
import { useStill } from "@/hooks/use-still"
import type { VoiceAccess } from "@/hooks/use-voice-access"
import type { CodeToken } from "@/lib/code-tokens"
import type { VoiceStatus } from "@/types/round"

// Each voice-screen step's state: whose turn it is, the words Mira heard and whether the option
// is picked.
const VOICE: Record<string, [VoiceStatus, string | null, boolean]> = {
  vSpeaking: ["speaking", null, false],
  vListening: ["hearing", null, false],
  vThinking: ["thinking", DEMO_SAID.answer, false],
  vPicked: ["speaking", DEMO_SAID.answer, true],
  vYes: ["hearing", DEMO_SAID.yes, true],
  vMoving: ["speaking", DEMO_SAID.yes, true],
}

// The voice screen before it plays: Mira about to speak.
const BEFORE_VOICE: [VoiceStatus, string | null, boolean] = [
  "speaking",
  null,
  false,
]

/** The microphone's state on the voice start page at step `index`. */
function accessAt(index: number): VoiceAccess {
  if (index < VOICE_START) {
    return "ask"
  }

  if (index >= stepIndex(STEPS, "vGranted")) {
    return "granted"
  }

  return index >= stepIndex(STEPS, "vAllow") ? "asking" : "ask"
}

/** What a candidate sees, played by a pointer in one panel, in click mode and then in voice mode,
 * the switch above it showing which; a visitor can switch to either. Click mode: the start page,
 * the pledge ticked and started, a question answered by a tap and Next. Voice mode: the start
 * page, the microphone and sound allowed in the browser's prompt, started, and the voice screen:
 * Mira reads, the candidate answers, she thinks, picks it, hears a yes and moves on. The screens
 * lie on top of each other, so the panel is as tall as the tallest and never changes size. With
 * reduced motion, each mode's last frame. */
export function CandidatesDemo({
  exampleColors,
}: {
  // Each click-mode question's example in its colors, made on the server.
  exampleColors: (CodeToken[][] | null)[]
}) {
  const interviews = useTranslations("interviews")
  const { ref, index: playing, jumpTo } = useDemoSteps<HTMLDivElement>(STEPS)
  const still = useStill()
  // With reduced motion, the mode a visitor chose shows its last frame.
  const [stillAt, setStillAt] = useState<number | null>(null)
  const index = still && stillAt !== null ? stillAt : playing
  const step = STEPS[index]
  const after = (name: string) => index >= stepIndex(STEPS, name)
  // What the pointer moves to: found in the screen shown when the pointer looks for it.
  const [targets] = useState(() =>
    Object.fromEntries(
      Object.entries(TARGETS).map(([name, selector]) => [
        name,
        {
          get current() {
            return (
              ref.current?.querySelector<HTMLElement>(
                `[data-shown=true] ${selector}`
              ) ?? null
            )
          },
        },
      ])
    )
  )
  const point = pointedAt(STEPS, index)
  const voice = step.voice

  function choose(toVoice: boolean) {
    const to = toVoice ? VOICE_START : CLICK_START

    if (still) {
      setStillAt(toVoice ? STEPS.length - 1 : VOICE_START - 1)
    } else {
      jumpTo(to)
    }
  }

  // A screen, shown while it's the step's, fading in after the one before has faded out.
  function screen(shown: boolean, content: React.ReactNode, key?: string) {
    return (
      <div
        key={key}
        data-shown={shown}
        className={cn(
          "flex min-h-0 flex-col transition-[opacity,translate,visibility]",
          shown
            ? "delay-200 duration-500"
            : "invisible translate-y-2 opacity-0 duration-200"
        )}
      >
        {content}
      </div>
    )
  }

  const [status, heard, voicePicked] = VOICE[step.name] ?? BEFORE_VOICE

  return (
    // The switch sits above the picture, overlapping its top edge by a third of its height, so it
    // never moves the picture.
    <div
      data-testid="candidates-demo"
      data-step={step.name}
      className="relative mx-auto w-full max-w-5xl"
    >
      <div className="absolute start-1/2 top-0 z-20 w-max -translate-x-1/2 -translate-y-2/3 rtl:translate-x-1/2">
        <AnswerModeSwitch
          label={interviews("answerMode")}
          voice={voice}
          disabled={false}
          onChange={choose}
        />
      </div>
      <div className="w-full">
        <DemoPanel ref={ref}>
          <DemoPointer
            target={targets[point ?? ""] ?? null}
            clicking={step.click === true}
            click={index}
          />
          <DemoMicPrompt
            open={["vAllow", "vPrompt", "vAimPrompt", "vPromptAllow"].includes(
              step.name
            )}
            pressed={step.name === "vPromptAllow"}
          />
          {/* One fixed height for every screen of both modes, the tallest's (the voice screen
              with Mute), so the page never moves as they change. */}
          <div className="grid h-[54rem] grid-cols-[minmax(0,1fr)] grid-rows-[minmax(0,1fr)] p-2 pt-5 *:min-w-0 *:[grid-area:1/1] max-sm:h-[49rem] sm:p-5 lg:h-[42rem]">
            {screen(
              !voice && step.screen === "start",
              <DemoInvitation
                voice={false}
                action={
                  <DemoStartAction
                    access={null}
                    pledged={voice || after("cPledge")}
                    pressed={step.name === "cStart"}
                  />
                }
              />
            )}
            {CLICK_QUESTIONS.map((question, at) => {
              const shown = step.screen === `q${at}`

              return screen(
                shown,
                <DemoClickSession
                  question={question}
                  exampleColors={exampleColors[at]}
                  active={shown}
                  // Unseen, a question keeps its picks, so it fades out as it was left.
                  picked={shown ? step.picked : question.picks}
                  pressed={step.name === `next${at}`}
                />,
                `q${at}`
              )
            })}
            {screen(
              voice && step.screen === "start",
              <DemoInvitation
                voice
                action={
                  <DemoStartAction
                    access={accessAt(index)}
                    pledged={voice && after("vPledge")}
                    pressed={step.name === "vStart"}
                  />
                }
              />
            )}
            {screen(
              voice && step.screen === "voice",
              <DemoVoiceSession
                active={voice && step.screen === "voice"}
                status={status}
                heard={heard}
                picked={voicePicked}
              />
            )}
          </div>
        </DemoPanel>
      </div>
    </div>
  )
}
