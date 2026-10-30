import type { components } from "@/types/api/rounds"

type Schemas = components["schemas"]

export type ReviewItem = Schemas["ReviewItem"]
export type NextQuestion = Schemas["NextQuestion"]
export type VoiceAnswer = Schemas["VoiceAnswerOut"]
export type AnswerInput = Omit<Schemas["AnswerCreate"], "question_id">
export type PracticeStart = Schemas["PracticeStartOut"]
export type PracticeRound = Schemas["PracticeRoundOut"]
export type PracticeRoundSummary = Schemas["PracticeRoundSummary"]
export type PracticeTopicProgress = Schemas["PracticeTopicProgress"]
export type PracticeStatus = Schemas["PracticeStatusOut"]
export type PracticeSize = Schemas["PracticeSizeOut"]
export type PracticeTiming = Schemas["PracticeTimingOut"]
export type PracticeTimingId = Schemas["PracticeStartIn"]["timing"]

// What Mira, the AI interviewer, is doing, as the screen shows it. "blocked": the browser holds
// the sound back until a tap (the page was reloaded).
export type VoiceStatus =
  | "off"
  | "starting"
  | "speaking"
  | "listening"
  | "hearing"
  | "thinking"
  | "blocked"
  | "unavailable"

export type VoiceHandlers = {
  // The options a spoken answer chose for the question, shown as picked.
  onPick: (question: string, picks: number[]) => void
  // A yes to the choice on screen: it's sent, as Next question does; whether it moved on.
  onConfirm: () => Promise<boolean>
  // The service's refusal (a limit, a failure), for the screen.
  failedMessage: string
}

// What Mira says before the next question: an answer was sent, or the question's time ran out.
export type VoiceAnnouncement = "next" | "time-up"
