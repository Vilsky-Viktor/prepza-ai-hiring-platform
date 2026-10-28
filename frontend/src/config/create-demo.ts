// The home page's "create an interview" demo: what its three panels show. Display only.

// The job description typed into the box.
export const DEMO_DESCRIPTION =
  "Senior Python developer for our payments team: async code, FastAPI services and PostgreSQL."

// The topics proposed for it, one for each skill it names; the one given a new subtopic by
// hand; the change asked of the AI and the topic it adds, which the description doesn't name.
export const DEMO_TOPICS = [
  { name: "Python and async code", subtopics: ["asyncio", "Testing"] },
  { name: "FastAPI services", subtopics: ["REST design", "Auth"] },
  { name: "PostgreSQL", subtopics: ["Indexes", "Transactions"] },
]

export const DEMO_EDITED = "PostgreSQL"
export const DEMO_ADDED_SUBTOPIC = "Migrations"
export const DEMO_CHANGE = "Add a topic on mentoring"
export const DEMO_NEW_TOPIC = {
  name: "Mentoring",
  subtopics: ["Code reviews", "Feedback"],
}

// The interview it makes: its title, each topic's questions (as many as an interview's topic
// gets) and how many each candidate gets of them, and the time for each question.
export const DEMO_INTERVIEW = {
  title: "Senior Python Developer",
  topicQuestions: 70,
  perCandidate: 10,
  questionSeconds: 60,
}

// The candidate invited to it.
export const DEMO_INVITE_EMAIL = "maria@example.com"
