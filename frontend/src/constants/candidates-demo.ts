// The home page's "what candidates see" picture: an invitation to an interview, then three of
// its questions. Display only.

// The inviting company, the interview and its times: 4 topics of 10 questions, a minute each.
export const DEMO_COMPANY = "Acme"
export const DEMO_TITLE = "Data Analyst"
export const DEMO_QUESTION_SECONDS = 60
export const DEMO_TOTAL_MINUTES = 40
export const DEMO_SECTIONS = 4
export const DEMO_SECTION_QUESTIONS = 10

// Each question: its topic and that topic's place, how many of its questions are answered, its
// text and, for a practical one, the example it shows (in `language`); its options and the
// ones picked, in turn (a multi-answer question ticks several).
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

export const DEMO_QUESTIONS: DemoQuestion[] = [
  {
    topic: "Statistics",
    section: 1,
    answered: 3,
    text: "Which measure is least affected by outliers?",
    options: ["Mean", "Median", "Range", "Standard deviation"],
    picks: [1],
  },
  {
    topic: "Statistics",
    section: 1,
    answered: 4,
    text: "Which of these can make an average misleading?",
    options: [
      "A few extreme values",
      "A skewed distribution",
      "A large sample size",
      "Rounding it to two decimals",
    ],
    picks: [0, 1],
    multi: true,
  },
  {
    // North's rows sum to 180, South's to 80: only North passes HAVING.
    topic: "SQL",
    section: 2,
    answered: 0,
    text: "What does this query return?",
    example: {
      code: [
        "-- orders(region, amount):",
        "-- North 120, South 80, North 60",
        "SELECT region FROM orders GROUP BY",
        "  region HAVING SUM(amount) > 100;",
      ].join("\n"),
      language: "sql",
    },
    options: ["North", "South", "North, South", "No rows"],
    picks: [0],
  },
]

// The facts under the picture, by their text's key.
export const CANDIDATE_NOTES = [
  "language",
  "phone",
  "time",
  "extraTime",
] as const
