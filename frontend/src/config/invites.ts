// The invite dialog's tabs: one email with a name, a list, or a file. The last one used is kept
// in this browser under INVITE_TAB_KEY.
export const INVITE_TABS = ["one", "many", "file"] as const
export type InviteTab = (typeof INVITE_TABS)[number]
export const INVITE_TAB_KEY = "prepza.invite-tab"

// A list as the backend reads it: an email per line, with or without a name. The example files
// (public/examples) hold the same candidates.
export const INVITE_EXAMPLE_LINES = [
  "ann@example.com",
  "Ann Lee <ann.lee@example.com>",
  "bob@example.com, Bob Stone",
]

// The example files the file tab downloads.
export const INVITE_EXAMPLES = [
  { href: "/examples/prepza-candidates-example.csv", label: "exampleCsv" },
  { href: "/examples/prepza-candidates-example.txt", label: "exampleTxt" },
] as const

// How many unusable lines of a list the dialog names; the rest are counted.
export const SHOWN_LINE_PROBLEMS = 10
