// The home page's "what candidates see" demo: its steps, in click mode and then in voice mode,
// and where its pointer's targets are.
import { CLICK_QUESTIONS, type DemoQuestion } from "@/config/candidates-demo"
import type { DemoStep } from "@/hooks/use-demo-steps"

// A step's mode, its screen (the start page, a click-mode question by its place, or the voice
// screen) and the options picked on it so far.
export type CandidateStep = DemoStep & {
  voice: boolean
  screen: string
  picked: number[]
}

const click = (step: DemoStep, screen: string, picked: number[] = []) => ({
  ...step,
  voice: false,
  screen,
  picked,
})
const voice = (step: DemoStep, screen: string) => ({
  ...step,
  voice: true,
  screen,
  picked: [],
})

/** A click-mode question's steps: read, each pick aimed at and clicked, then Next. */
function questionSteps(question: DemoQuestion, at: number): CandidateStep[] {
  const screen = `q${at}`
  const read = question.example ? 3000 : 1800
  const picks = question.picks.flatMap((option, index) => {
    const before = question.picks.slice(0, index)

    return [
      click(
        { name: `aim${at}-${index}`, ms: 900, point: `option${option}` },
        screen,
        before
      ),
      click({ name: `pick${at}-${index}`, ms: 450, click: true }, screen, [
        ...before,
        option,
      ]),
    ]
  })

  return [
    click({ name: `read${at}`, ms: read, point: "none" }, screen),
    ...picks,
    click({ name: `picked${at}`, ms: 500 }, screen, question.picks),
    click(
      { name: `aimNext${at}`, ms: 700, point: "next" },
      screen,
      question.picks
    ),
    click({ name: `next${at}`, ms: 450, click: true }, screen, question.picks),
  ]
}

// Click mode: the start page read, the pledge ticked and the interview started; each question
// read, answered and Next. Voice mode: the start page read, the microphone and sound allowed in
// the browser's prompt, the pledge ticked and started; Mira reads the question, the candidate
// answers, she thinks and picks the option, asks for a yes, hears it and moves on.
export const STEPS: CandidateStep[] = [
  click({ name: "cInvite", ms: 1600, point: "title" }, "start"),
  click({ name: "cAimPledge", ms: 800, point: "pledge" }, "start"),
  click({ name: "cPledge", ms: 400, click: true }, "start"),
  click({ name: "cAimStart", ms: 700, point: "start" }, "start"),
  click({ name: "cStart", ms: 450, click: true }, "start"),
  ...CLICK_QUESTIONS.flatMap(questionSteps),
  voice({ name: "vInvite", ms: 1600, point: "title" }, "start"),
  voice({ name: "vAimAllow", ms: 800, point: "allow" }, "start"),
  voice({ name: "vAllow", ms: 400, click: true }, "start"),
  voice({ name: "vPrompt", ms: 700 }, "start"),
  voice({ name: "vAimPrompt", ms: 800, point: "promptAllow" }, "start"),
  voice({ name: "vPromptAllow", ms: 400, click: true }, "start"),
  voice({ name: "vGranted", ms: 800, point: "none" }, "start"),
  voice({ name: "vAimPledge", ms: 700, point: "pledge" }, "start"),
  voice({ name: "vPledge", ms: 400, click: true }, "start"),
  voice({ name: "vAimStart", ms: 700, point: "start" }, "start"),
  voice({ name: "vStart", ms: 450, click: true }, "start"),
  voice({ name: "vSpeaking", ms: 2800, point: "none" }, "voice"),
  voice({ name: "vListening", ms: 1800 }, "voice"),
  voice({ name: "vThinking", ms: 1600 }, "voice"),
  voice({ name: "vPicked", ms: 2200 }, "voice"),
  voice({ name: "vYes", ms: 1400 }, "voice"),
  voice({ name: "vMoving", ms: 1800 }, "voice"),
]

// Where each mode starts.
export const CLICK_START = 0
export const VOICE_START = STEPS.findIndex((step) => step.voice)

// What the pointer moves to, found in the demo by these selectors.
export const TARGETS = {
  title: "[data-demo-target=title]",
  pledge: "[data-demo-target=pledge]",
  start: "[data-demo-target=start]",
  ...Object.fromEntries(
    [0, 1, 2, 3].map((option) => [
      `option${option}`,
      `[data-demo-target=options] li:nth-child(${option + 1}) button`,
    ])
  ),
  next: "[data-demo-target=next]",
  allow: "[data-demo-target=access] button",
  promptAllow: "[data-demo-target=promptAllow]",
}
