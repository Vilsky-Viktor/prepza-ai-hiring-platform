// The question's countdown turns red for its last seconds.
export const COUNTDOWN_WARNING_SECONDS = 10

// How an interview's candidates can be listed; the first is the default, as in the API.
export const CANDIDATE_SORTS = ["grade", "date"] as const

// The mark the generation page adds to an interview's address when it's ready: it shows
// "What's next" once.
export const READY_PARAM = "ready"

export type CandidateSort = (typeof CANDIDATE_SORTS)[number]
