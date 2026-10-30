// The home page's "create an interview" demo: what its three panels show. Display only.

// The job description pasted into the box, as a real job ad reads, its lines kept.
export const DEMO_DESCRIPTION = [
  "Acme helps online shops answer their customers with AI.",
  "We're hiring an AI Engineer to build our LLM features.",
  "• 3+ years of Python",
  "• LLM apps, RAG and vector search",
  "• Evaluating and monitoring models",
  "Remote, flexible hours, a learning budget.",
].join("\n")

// The four topics proposed for it, one for each skill it names; the one given a new subtopic by
// hand; the change asked of the AI and the fifth topic it adds.
export const DEMO_TOPICS = [
  {
    name: "LLM fundamentals",
    subtopics: ["Tokens", "Prompting", "Context windows"],
  },
  {
    name: "Retrieval-augmented generation",
    subtopics: ["Embeddings", "Chunking", "Vector search"],
  },
  { name: "Python for ML systems", subtopics: ["asyncio", "Type hints"] },
  {
    name: "Deploying and monitoring models",
    subtopics: ["Latency", "Costs", "Drift"],
  },
]

export const DEMO_EDITED = "Python for ML systems"
export const DEMO_ADDED_SUBTOPIC = "Testing"
export const DEMO_CHANGE = "Add a topic on evaluating LLM output"
export const DEMO_NEW_TOPIC = {
  name: "LLM evaluation",
  subtopics: ["Test sets", "LLM as judge", "Metrics"],
}

// The company a first-time user names before the interview is made.
export const DEMO_COMPANY = "Acme"

// The interview it makes: its title, each topic's questions (as many as an interview's topic
// gets) and how many each candidate gets of them, and the time for each question.
export const DEMO_INTERVIEW = {
  title: "AI Engineer",
  topicQuestions: 70,
  perCandidate: 10,
  questionSeconds: 60,
}

// The questions each candidate gets, changed on two of its topics before inviting: more on one,
// and none on another, which leaves that topic out.
export const DEMO_LIMITS = [
  { topic: "Retrieval-augmented generation", limit: 15 },
  { topic: "LLM fundamentals", limit: 0 },
]

// The candidate invited to it, and the example name in the invite's empty name field.
export const DEMO_INVITE_EMAIL = "maria@example.com"
export const DEMO_INVITE_NAME = "Maria Garcia"
