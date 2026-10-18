// The developer docs' MCP tab: its English text (the docs are English only), the apps beyond
// the AI apps page's, and the example agents, whose files live in content/mcp/<language>/.

export const MCP_TOOLS_PATH = "/assistant/mcp/tools"
export const MCP_EXAMPLES_DIR = "content/mcp"

// The examples' languages, in the order the editor's language menu lists them.
export const MCP_LANGUAGES = ["python", "typescript"] as const

export const MCP_TITLES = {
  server: "Server",
  apps: "AI apps",
  agents: "Your own agent",
  updates: "Daily updates",
  tools: "Tools",
  rules: "Rules",
  connections: "Managing connections",
}

export const MCP_INTRO =
  "Connect prepza to an AI app or to your own agent through its MCP server. The server offers the tools of prepza's own assistant: the agent asks about your companies, interviews and candidates, and makes changes, as you, with exactly your roles, in every company you're in. No model runs on prepza's side."

export const MCP_SERVER = `The server speaks the Model Context Protocol over Streamable HTTP, statelessly: no sessions to keep, and any request can go to any instance.

**Signing in as you.** An AI app, or an agent you run on your own computer, signs in with OAuth 2.1 (PKCE and dynamic client registration): it opens prepza's consent page once, you choose Allow, and no key is pasted anywhere. The access token lasts an hour and the refresh token 90 days. Each refresh replaces both, so keep the new ones, or the agent has to ask you again. One token never serves two agents at once.

**Signing in with an API key.** An agent on a server, with no browser, sends a company API key instead: \`Authorization: Bearer pz_...\`. The key needs the **mcp** permission, ticked when it's made on the company's API page. It acts as the member who made it, in its company only, and gets only the tools its other permissions allow (see Tools). Its calls count against the company's API limit.`

export const MCP_OTHER_APPS = [
  {
    label: "Gemini CLI",
    text: "Add the server to `~/.gemini/settings.json`, then run `/mcp auth prepza` in Gemini CLI and allow it on the prepza page that opens.",
    code: '{\n  "mcpServers": {\n    "prepza": { "httpUrl": "{url}" }\n  }\n}',
  },
  {
    label: "Cursor",
    text: "Add the server to `~/.cursor/mcp.json` (or the project's `.cursor/mcp.json`), choose **Connect** next to prepza in Cursor's MCP settings, and allow it on the prepza page that opens.",
    code: '{\n  "mcpServers": {\n    "prepza": { "url": "{url}" }\n  }\n}',
  },
  {
    label: "VS Code",
    text: "With GitHub Copilot: add the server to the project's `.vscode/mcp.json`, choose **Start** above prepza, and allow it on the prepza page that opens.",
    code: '{\n  "servers": {\n    "prepza": { "type": "http", "url": "{url}" }\n  }\n}',
  },
  {
    label: "Le Chat",
    text: "In Le Chat, open **Intelligence → Connectors → Add connector → Custom MCP connector**, paste the server address, choose **Connect**, and allow it on the prepza page that opens.",
    code: null,
  },
]

export const MCP_UPDATES = `Ask your AI app "What's new in prepza?" and it calls \`get_updates\`: what happened in your companies since that app last checked (the first time, the last 7 days). A short summary comes first, then each candidate who started or finished, with their grade and whether they passed, invites that weren't delivered, candidates from your ATS who couldn't be invited, questions flagged or fixed, interviews that are ready, the rest of your notifications, and companies running low on credits that no automatic top-up refills. Each app and each API key keeps its own last check, so every update reaches it once, and checking doesn't mark anything as read in prepza. Only companies that allow AI apps are included; an API key needs the \`candidates:read\` permission, and \`credits:read\` to hear about credits.

**Every morning, by itself.** In an app with scheduled tasks, such as ChatGPT's, add a daily task like: "Every weekday at 9:00, call prepza's get_updates and tell me who started, who finished, who passed and what needs my attention." The app then brings you the summary without being asked.`

export const MCP_AGENTS =
  "Complete examples in Python and TypeScript. They share one sign-in file: with `PREPZA_API_KEY` set it signs in with that key; otherwise it opens prepza's consent page in your browser once and keeps the tokens in `prepza-tokens.json`, updating them at each refresh. Each file's first line installs the versions it was run with."

export const MCP_EXAMPLES = [
  {
    key: "auth",
    title: "Sign-in",
    text: "Shared by the three agents below.",
    files: { python: "prepza_auth.py", typescript: "prepza-auth.ts" },
  },
  {
    key: "langgraph",
    title: "LangGraph",
    text: "prepza's tools in a graph of your own: the model, then a ToolNode, until it answers.",
    files: { python: "langgraph_agent.py", typescript: "langgraph-agent.ts" },
  },
  {
    key: "langchain",
    title: "LangChain",
    text: "prepza's tools in a LangChain agent.",
    files: { python: "langchain_agent.py", typescript: "langchain-agent.ts" },
  },
  {
    key: "llamaindex",
    title: "LlamaIndex",
    text: "prepza's tools in a LlamaIndex agent.",
    files: { python: "llamaindex_agent.py", typescript: "llamaindex-agent.ts" },
  },
]

export const MCP_TOOLS_TEXT =
  "What an agent can call, and whether each tool only reads or changes something (`readOnlyHint`, `destructiveHint`), so you know what to allow. Deleting an account or a company is done in prepza only. An API key gets a tool only with the permission it names."

// {minute}, {day} and {writes}: the limits, from the server.
export const MCP_RULES = `**Limits.** A user's apps and agents together make up to {minute} calls a minute and {day} a day, and {writes} changes an hour, counted with those made in prepza's assistant.

**Errors** come back as results with \`isError\` and the reason in the user's language, for the agent to explain.

**A company can turn AI apps off** on its AI apps page: its data then answers \`403\` with the reason, to API keys too.

**Secrets** such as passwords and API keys in a tool's arguments are refused before anything is sent.

**Links.** A result carries \`links\` to the prepza pages that show it.`

export const MCP_CONNECTIONS =
  "Every company's Integrations → AI apps page lists the apps you connected; Disconnect stops one at once. To stop an agent signed in with an API key, delete the key on the company's API page."

// The tool list's labels.
export const MCP_TOOL_LABELS = {
  reads: "reads",
  changes: "changes",
  destructive: "can't be undone",
  noKey: "not for API keys",
}
