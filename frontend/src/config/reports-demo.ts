// The home page's "see who's best, share it in seconds" picture: an interview's candidates, two
// of their pages, the chat their summaries go to and the interview's notes. Display only.
import type { CandidateRowData } from "@/components/common/candidate-row"

// The interview, its company (named in the chat summaries) and its passing grade.
export const DEMO_REPORT_INTERVIEW = {
  title: "Product Manager",
  topics: 10,
  questions: 700,
}
export const DEMO_REPORT_COMPANY = "Acme"
export const DEMO_PASS_MARK = 70
// How many candidates the interview has; the list shows its first few.
export const DEMO_CANDIDATE_COUNT = 73
// How many notes it has before the new one; the notes tab shows the newest few.
export const DEMO_NOTE_COUNT = 15

// A topic of a candidate's page: its grade, the signals the browser reported on it, and one of
// its questions as they answered it: the option picked (and the right one), how many seconds it
// took and whether that was too fast, and the signals while it was open.
export type DemoTopic = {
  title: string
  grade: number
  tab_leaves: number
  copies: number
  fast_answers: number
  question?: {
    text: string
    options: string[]
    pick: number
    right: number
    seconds: number
    fast?: boolean
    tab_leaves?: number
    copies?: number
  }
}

// The questions answered, one for each topic, as their text and options.
const QUESTIONS = {
  strategy: {
    text: "What should come first before building a new feature?",
    options: [
      "Checking the problem with users",
      "Writing the technical spec",
      "Setting the launch date",
      "Designing the screens",
    ],
  },
  metrics: {
    text: "Conversion fell from 4% to 3%. How much is that, relative to before?",
    options: ["1%", "25%", "33%", "75%"],
  },
  stakeholders: {
    text: "A partner team disagrees with your priorities. What do you do first?",
    options: [
      "Escalate to your manager",
      "Ask what they need and why",
      "Keep your plan as it is",
      "Drop your priorities",
    ],
  },
}

// A candidate in the list and, for the two opened, their page: their topics (the grades average
// to theirs, the signals add up to the row's) and what their answers show.
export type DemoCandidate = CandidateRowData & {
  name: string
  status: "finished" | "in_process"
  grade: number | null
  passed: boolean | null
  progress: number
  topics?: DemoTopic[]
  patterns?: {
    personFit?: {
      hardRight: number
      hard: number
      easyWrong: number
      easy: number
    }
    timing?: boolean
    followUp: { topic: string; text: string; right: string; wrong: string }
  }
}

// The interview's ten topics.
const TOPICS = [
  "Product strategy",
  "Metrics",
  "Stakeholders",
  "Roadmapping",
  "User research",
  "Prioritisation",
  "Experimentation",
  "Pricing",
  "Go-to-market",
  "Communication",
]

// Each opened candidate's topics, in TOPICS' order: grade, page leaves, copies, fast answers.
// The grades average to the candidate's; the signals add up to the list's.
const BEST_TOPICS = [94, 88, 91, 90, 93, 89, 92, 90, 91, 92].map((grade) => [
  grade,
  0,
  0,
  0,
])
const FLAGGED_TOPICS = [
  [89, 2, 1, 2],
  [84, 1, 1, 2],
  [88, 1, 1, 1],
  [86, 1, 0, 1],
  [90, 1, 1, 1],
  [85, 1, 0, 1],
  [87, 1, 1, 1],
  [86, 0, 0, 1],
  [88, 1, 1, 1],
  [87, 0, 0, 1],
]

// The question shown under each of the first topics, as each candidate answered it.
const BEST_QUESTIONS: DemoTopic["question"][] = [
  { ...QUESTIONS.strategy, pick: 0, right: 0, seconds: 38 },
  { ...QUESTIONS.metrics, pick: 1, right: 1, seconds: 47 },
  { ...QUESTIONS.stakeholders, pick: 1, right: 1, seconds: 29 },
]
const FLAGGED_QUESTIONS: DemoTopic["question"][] = [
  {
    ...QUESTIONS.strategy,
    pick: 0,
    right: 0,
    seconds: 3,
    fast: true,
    tab_leaves: 2,
    copies: 1,
  },
  {
    ...QUESTIONS.metrics,
    pick: 1,
    right: 1,
    seconds: 4,
    fast: true,
    tab_leaves: 1,
  },
  { ...QUESTIONS.stakeholders, pick: 1, right: 1, seconds: 3, fast: true },
]

/** A candidate's topics from their numbers, the first ones with their question. */
function topicsOf(numbers: number[][], questions: DemoTopic["question"][]) {
  return numbers.map(([grade, tab_leaves, copies, fast_answers], index) => ({
    title: TOPICS[index],
    grade,
    tab_leaves,
    copies,
    fast_answers,
    question: questions[index],
  }))
}

export const DEMO_REPORT_CANDIDATES: DemoCandidate[] = [
  {
    name: "Liam Chen",
    email: "liam.chen@example.com",
    status: "finished",
    progress: 100,
    grade: 91,
    passed: true,
    tab_leaves: 0,
    copies: 0,
    fast_answers: 0,
    topics: topicsOf(BEST_TOPICS, BEST_QUESTIONS),
  },
  {
    name: "Ethan Brooks",
    email: "ethan.brooks@example.com",
    status: "finished",
    progress: 100,
    grade: 87,
    passed: true,
    tab_leaves: 9,
    copies: 6,
    fast_answers: 12,
    topics: topicsOf(FLAGGED_TOPICS, FLAGGED_QUESTIONS),
    patterns: {
      personFit: { hardRight: 9, hard: 10, easyWrong: 4, easy: 10 },
      timing: true,
      followUp: {
        topic: TOPICS[1],
        text: QUESTIONS.metrics.text,
        right: "25%",
        wrong: "1%",
      },
    },
  },
  {
    name: "Emma Larsen",
    email: "emma.larsen@example.com",
    status: "finished",
    progress: 100,
    grade: 84,
    passed: true,
    tab_leaves: 0,
    copies: 0,
    fast_answers: 1,
  },
  {
    name: "Daniel Okafor",
    email: "daniel.okafor@example.com",
    status: "finished",
    progress: 100,
    grade: 62,
    passed: false,
    tab_leaves: 1,
    copies: 0,
    fast_answers: 0,
  },
  {
    name: "Sofia Marquez",
    email: "sofia.marquez@example.com",
    status: "in_process",
    progress: 40,
    grade: null,
    passed: null,
    tab_leaves: 0,
    copies: 0,
    fast_answers: 0,
  },
]

// The best candidate, the one with many signals, and the runner-up the team also proceeds with.
export const DEMO_BEST = 0
export const DEMO_FLAGGED = 1
export const DEMO_RUNNER_UP = 2

// Who the list's report is emailed to, and the PDF's name.
export const DEMO_SHARE_EMAIL = "lisa@example.com"
export const DEMO_PDF = "product-manager-candidates.pdf"

// The chat the summaries go to, and when each message shows.
export const DEMO_CHAT = { name: "Hiring team", initials: "HT" }
export const DEMO_CHAT_TIMES = ["10:24", "10:25", "10:31", "10:32"]

// The interview's earlier notes from teammates, and how many hours ago each was written.
export const DEMO_NOTES = [
  {
    author: "Maya Patel",
    hoursAgo: 26,
    text: "Hiring manager wants a shortlist of two by Friday.",
  },
  {
    author: "Tom Becker",
    hoursAgo: 3,
    text: "Daniel was strong on stakeholders in the phone screen; weaker on metrics.",
  },
  {
    author: "Maya Patel",
    hoursAgo: 1,
    text: "Sofia asked for more time; I'll check in tomorrow.",
  },
]

// The member writing the new note.
export const DEMO_AUTHOR = "Lisa Novak"
