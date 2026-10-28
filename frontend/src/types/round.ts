import type { components } from "@/types/api/rounds"

type Schemas = components["schemas"]

export type ReviewItem = Schemas["ReviewItem"]
export type NextQuestion = Schemas["NextQuestion"]
export type AnswerInput = Omit<Schemas["AnswerCreate"], "question_id">
export type PracticeStart = Schemas["PracticeStartOut"]
export type PracticeRound = Schemas["PracticeRoundOut"]
export type PracticeRoundSummary = Schemas["PracticeRoundSummary"]
export type PracticeTopicProgress = Schemas["PracticeTopicProgress"]
export type PracticeStatus = Schemas["PracticeStatusOut"]
export type PracticeSize = Schemas["PracticeSizeOut"]
export type PracticeTiming = Schemas["PracticeTimingOut"]
export type PracticeTimingId = Schemas["PracticeStartIn"]["timing"]
