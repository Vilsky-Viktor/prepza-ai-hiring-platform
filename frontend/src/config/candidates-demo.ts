// The home page's "what candidates see" picture: an invitation to an interview and one of its
// questions, in click mode and then in voice mode. Display only.

// The inviting company, the interview and its times: 4 topics of 10 questions, a minute each.
export const DEMO_COMPANY = "Acme"
export const DEMO_TITLE = "Data Analyst"
export const DEMO_QUESTION_SECONDS = 60
export const DEMO_TOTAL_MINUTES = 40
export const DEMO_SECTIONS = 4
export const DEMO_SECTION_QUESTIONS = 10

// A question as a candidate plays it: its topic and that topic's place, how many of its
// questions are answered, its text and, for a practical one, the example it shows (in
// `language`); its options and the ones picked, in turn (a multi-answer question ticks several).
export type DemoQuestion = {
  topic: string
  section: number
  answered: number
  text: string
  example?: { code: string; language: string }
  options: string[]
  picks: number[]
  multi?: boolean
}

// The questions answered in click mode: one answer, several, and one with an example.
export const CLICK_QUESTIONS: DemoQuestion[] = [
  {
    topic: "Statistics",
    section: 1,
    answered: 3,
    text: "A few very large orders are skewing your average order value. Which measure describes a typical order best?",
    options: [
      "The mean order value",
      "The median order value",
      "The range of order values",
      "The standard deviation of order values",
    ],
    picks: [1],
  },
  {
    topic: "Statistics",
    section: 1,
    answered: 4,
    text: "Weekly revenue on your dashboard dropped 20% right after a data pipeline change. Which checks would you run first?",
    options: [
      "Compare row counts before and after the change",
      "Look for duplicated or missing dates",
      "Change the dashboard's colour scheme",
      "Ask sales whether customers stopped buying",
    ],
    picks: [0, 1],
    multi: true,
  },
  {
    // North's rows sum to 180, South's to 80: only North passes HAVING.
    topic: "SQL",
    section: 2,
    answered: 0,
    text: "Marketing wants the regions whose total sales pass 100. What does this query return?",
    example: {
      code: [
        "-- orders(region, amount):",
        "-- North 120, South 80, North 60",
        "SELECT region FROM orders GROUP BY",
        "  region HAVING SUM(amount) > 100;",
      ].join("\n"),
      language: "sql",
    },
    options: ["North only", "South only", "North and South", "No rows"],
    picks: [0],
  },
]

// The question Mira reads in voice mode, and what the candidate says: the answer, then the
// yes that confirms it.
export const VOICE_QUESTION: DemoQuestion = {
  topic: "Visualisation",
  section: 2,
  answered: 5,
  text: "You need to show how monthly sign-ups changed over the last two years. Which chart shows that trend best?",
  options: [
    "A pie chart of sign-ups by month",
    "A line chart of sign-ups by month",
    "A scatter plot of sign-ups against revenue",
    "A histogram of monthly sign-up counts",
  ],
  picks: [1],
}
export const DEMO_SAID = { answer: "The line chart", yes: "Yes" }

// The site asking for the microphone in the browser's prompt.
export const DEMO_SITE = "prepza.ai"

// The facts under the picture, by their text's key.
export const CANDIDATE_NOTES = ["modes", "phone", "time", "extraTime"] as const
