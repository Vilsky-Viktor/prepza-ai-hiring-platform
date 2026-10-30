// The home page's "create an interview" demo: its steps, and what its pointer moves to in each
// panel.
import {
  DEMO_ADDED_SUBTOPIC,
  DEMO_CHANGE,
  DEMO_COMPANY,
  DEMO_EDITED,
  DEMO_INVITE_EMAIL,
  DEMO_NEW_TOPIC,
  DEMO_TOPICS,
} from "@/config/create-demo"
import { type DemoStep, stepIndex } from "@/hooks/use-demo-steps"

// The topics the questions are written for: the adjusted ones, the edited one with its added
// subtopic.
export const ADJUSTED = [...DEMO_TOPICS, DEMO_NEW_TOPIC].map((topic) =>
  topic.name === DEMO_EDITED
    ? { ...topic, subtopics: [...topic.subtopics, DEMO_ADDED_SUBTOPIC] }
    : topic
)
export const WRITTEN = ADJUSTED.map(({ name }) => name)

// The pointer right-clicks the empty box, picks paste from its menu and the whole description
// shows, then it clicks send; a first company is named and it clicks continue, and the loading
// mark stands for the interview being made until it's ready. The topics show
// one by one; it opens a topic's editor, types a subtopic, adds it and closes the editor, then
// types into the request for changes and clicks apply, and a topic is added; then it clicks
// approve, the questions are written, topic by topic, and the interview is ready: it changes the
// questions each candidate gets on two topics, clicks to invite, the invite dialog opens, a
// candidate's email is typed and sent, and the "sent" notice shows. Last, the interview alone:
// the still frame.
export const STEPS: DemoStep[] = [
  { name: "empty", ms: 900, point: "field" },
  { name: "menu", ms: 300, click: true },
  { name: "aimPaste", ms: 700, point: "paste" },
  { name: "paste", ms: 400, click: true },
  { name: "pasted", ms: 900 },
  { name: "aim", ms: 800, point: "send" },
  { name: "send", ms: 500, click: true },
  { name: "company", ms: 900, point: "name" },
  { name: "focusName", ms: 300, click: true },
  { name: "naming", ms: 80, repeat: DEMO_COMPANY.length },
  { name: "aimContinue", ms: 700, point: "continue" },
  { name: "continue", ms: 500, click: true },
  { name: "sent", ms: 400, point: "none" },
  { name: "topics", ms: 400, repeat: DEMO_TOPICS.length },
  { name: "review", ms: 900, point: "edit" },
  { name: "open", ms: 400, click: true },
  { name: "aimSubtopic", ms: 700, point: "subtopic" },
  { name: "focusSubtopic", ms: 300, click: true },
  { name: "adding", ms: 90, repeat: DEMO_ADDED_SUBTOPIC.length },
  { name: "aimAdd", ms: 600, point: "add" },
  { name: "add", ms: 400, click: true },
  { name: "aimDone", ms: 600, point: "done" },
  { name: "done", ms: 400, click: true },
  { name: "edited", ms: 900, point: "ask" },
  { name: "ask", ms: 300, click: true },
  { name: "asking", ms: 50, repeat: DEMO_CHANGE.length },
  { name: "aimApply", ms: 800, point: "apply" },
  { name: "apply", ms: 500, click: true },
  { name: "applying", ms: 800, point: "none" },
  { name: "applied", ms: 1200 },
  { name: "aimGo", ms: 800, point: "apply" },
  { name: "go", ms: 500, click: true },
  { name: "writing", ms: 700, repeat: WRITTEN.length, point: "none" },
  { name: "written", ms: 1500 },
  { name: "ready", ms: 1200 },
  { name: "aimLimit0", ms: 800, point: "limit0" },
  { name: "focusLimit0", ms: 300, click: true },
  { name: "limit0", ms: 700 },
  { name: "aimLimit1", ms: 800, point: "limit1" },
  { name: "focusLimit1", ms: 300, click: true },
  { name: "limit1", ms: 700 },
  { name: "aimInvite", ms: 800, point: "invite" },
  { name: "invite", ms: 500, click: true },
  { name: "aimEmail", ms: 700, point: "email" },
  { name: "focusEmail", ms: 300, click: true },
  { name: "typingEmail", ms: 70, repeat: DEMO_INVITE_EMAIL.length },
  { name: "aimSendInvite", ms: 700, point: "sendInvite" },
  { name: "sendInvite", ms: 450, click: true },
  { name: "invited", ms: 2500, point: "none" },
  { name: "rest", ms: 600 },
]

// The steps the invite dialog is open for.
export const INVITING = [
  "aimEmail",
  "focusEmail",
  "typingEmail",
  "aimSendInvite",
  "sendInvite",
]

// What the pointer moves to, by name (`data-demo-target`).
export const TARGETS = [
  "field",
  "paste",
  "send",
  "name",
  "continue",
  "edit",
  "subtopic",
  "add",
  "done",
  "ask",
  "apply",
  "limit0",
  "limit1",
  "invite",
  "email",
  "sendInvite",
]

export const APPLIED = stepIndex(STEPS, "applied")
export const WRITING = stepIndex(STEPS, "writing")
export const READY = stepIndex(STEPS, "ready")
export const PASTED = stepIndex(STEPS, "pasted")
export const NAMING = stepIndex(STEPS, "company")
export const TOPICS = stepIndex(STEPS, "sent")
export const ADDED = stepIndex(STEPS, "aimDone")
