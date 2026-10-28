// The home page's "detailed reports and quick sharing" picture: an interview's candidates, one
// candidate's report and its answers, and the address the report is emailed to. Display only.

// The interview, its candidates' company (named in the chat summary) and its passing grade.
export const DEMO_REPORT_INTERVIEW = {
  title: "Product Manager",
  topics: 3,
  questions: 210,
}
export const DEMO_REPORT_COMPANY = "Acme"
export const DEMO_PASS_MARK = 70

// The candidates in the list; the first one's report is opened. A missing name shows the email.
export type DemoCandidate = {
  name: string | null
  email: string
  status: "finished" | "in_process" | "invited"
  progress: number
  grade: number | null
  passed: boolean | null
}

export const DEMO_REPORT_CANDIDATES: DemoCandidate[] = [
  {
    name: "Emma Larsen",
    email: "emma.larsen@example.com",
    status: "finished",
    progress: 100,
    grade: 84,
    passed: true,
  },
  {
    name: "Daniel Okafor",
    email: "daniel.okafor@example.com",
    status: "finished",
    progress: 100,
    grade: 62,
    passed: false,
  },
  {
    name: "Sofia Marquez",
    email: "sofia.marquez@example.com",
    status: "in_process",
    progress: 40,
    grade: null,
    passed: null,
  },
  {
    name: "Liam Chen",
    email: "liam.chen@example.com",
    status: "finished",
    progress: 100,
    grade: 91,
    passed: true,
  },
  {
    name: null,
    email: "noah.berg@example.com",
    status: "invited",
    progress: 0,
    grade: null,
    passed: null,
  },
]

// The candidate whose report opens.
export const DEMO_OPENED = 0

// Who the list's report is emailed to.
export const DEMO_SHARE_EMAIL = "lisa@example.com"

// The chat the summary goes to in WhatsApp, and the time its message shows.
export const DEMO_CHAT = {
  name: "Hiring team",
  initials: "HT",
  // When the team asked, and when the summary went out.
  asked: "10:21",
  time: "10:24",
}

// An answer in the report: its question, the options picked and whether each is right, its
// verdict and, for a multi-answer one, the right options picked of all and its points.
export type DemoAnswer = {
  text: string
  picks: { answer: string; correct: boolean }[]
  verdict: "correct" | "incorrect" | "partlyCorrect"
  multi?: { right: number; total: number; points: number }
}

// The opened candidate's topics: each one's grade, integrity signals and answers. Their grades
// average to the candidate's 84%.
export type DemoTopic = {
  title: string
  grade: number
  tab_leaves: number
  copies: number
  fast_answers: number
  answers: DemoAnswer[]
}

export const DEMO_REPORT_TOPICS: DemoTopic[] = [
  {
    title: "Product strategy",
    grade: 88,
    tab_leaves: 0,
    copies: 0,
    fast_answers: 0,
    answers: [
      {
        text: "What should come first before building a new feature?",
        picks: [{ answer: "Checking the problem with users", correct: true }],
        verdict: "correct",
      },
      {
        text: "Which of these are early signs that users will stay?",
        picks: [
          { answer: "Using the product every week", correct: true },
          { answer: "Inviting their teammates", correct: true },
        ],
        verdict: "partlyCorrect",
        multi: { right: 2, total: 3, points: 0.67 },
      },
    ],
  },
  {
    title: "Metrics",
    grade: 79,
    tab_leaves: 0,
    copies: 0,
    fast_answers: 1,
    answers: [
      {
        text: "Conversion fell from 4% to 3%. How much is that, relative to before?",
        picks: [{ answer: "1%", correct: false }],
        verdict: "incorrect",
      },
      {
        text: "Which number best shows that a new feature is useful?",
        picks: [
          { answer: "How many come back to use it again", correct: true },
        ],
        verdict: "correct",
      },
    ],
  },
  {
    title: "Stakeholders",
    grade: 85,
    tab_leaves: 0,
    copies: 0,
    fast_answers: 0,
    answers: [
      {
        text: "A partner team disagrees with your priorities. What do you do first?",
        picks: [{ answer: "Ask what they need and why", correct: true }],
        verdict: "correct",
      },
    ],
  },
]
