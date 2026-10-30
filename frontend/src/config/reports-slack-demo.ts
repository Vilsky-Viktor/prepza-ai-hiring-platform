// The home page's "see who's best" picture's last screen: the Slack channel prepza posts to.
// Display only.

// The channel prepza posts to in Slack, and the candidates' "finished" messages there (the only
// kind of this flow Slack gets: services/notifications/helpers/slack.py), oldest first, by
// their place in the list and when each came.
export const DEMO_SLACK_CHANNEL = "hiring"
// The app's name there and its button, as prepza posts them (in English, whatever the page's
// language).
export const DEMO_SLACK_APP = "prepza"
export const DEMO_SLACK_BUTTON = "Open in prepza"
// Slack's own words around them, in English as in an English workspace: the app tag, the
// channel's members and its message box.
export const DEMO_SLACK_UI = {
  app: "APP",
  members: 12,
  composer: "Message #hiring",
  channelsTitle: "Channels",
  peopleTitle: "Direct messages",
  appsTitle: "Apps",
}

// The workspace's side menu: its name, its channels (the current one is DEMO_SLACK_CHANNEL),
// teammates to message, whether each is active, and Slack's sidebar colours.
export const DEMO_SLACK_SIDEBAR = {
  workspace: "Acme",
  channels: ["general", "hiring", "engineering"],
  people: [
    { name: "Maya Patel", active: true },
    { name: "Tom Becker", active: false },
    { name: "Lisa Novak", active: true },
  ],
  // Slack's aubergine, and the blue of the open channel.
  background: "#3f0e40",
  current: "#1164a3",
  active: "#2bac76",
}
export const DEMO_SLACK_FINISHED = [
  { candidate: 3, time: "09:12" },
  { candidate: 2, time: "09:40" },
  { candidate: 1, time: "09:58" },
  { candidate: 0, time: "10:05" },
]
