---
title: "AI agents, MCP and APIs: what they are and how to use them in hiring"
seoTitle: "AI Agents, MCP and APIs in Hiring: What They Are and How to Use Them"
description: "What an AI agent is, what MCP and an API do, how to use them safely in hiring, and how to run prepza from its agent, from Claude and ChatGPT, or from your own platform."
updated: "2026-10-21"
---

# AI agents, MCP and APIs: what they are and how to use them in hiring

Most people first met AI as a chat window: you ask, it answers. An AI agent goes one step further. It can look things up in your tools and, when you ask, do things in them: create an interview, invite a list of candidates, tell you who scored highest last week. The Model Context Protocol (MCP) is the standard that lets the AI chat you already use, such as Claude or ChatGPT, connect to tools like these. And an API is the older, more precise way for software to talk to software, without AI in between.

This guide explains all three in plain terms, what they're good for in hiring, what to watch out for, and how to use them with prepza.

## What an AI agent is

A chatbot only writes text. An agent is a language model with **tools**: small, well-defined actions it may call, such as "list the candidates of this interview" or "invite this email". When you ask something, the agent decides which tools to use, reads what they return, and answers from that, not from memory.

| A chatbot | An AI agent |
| --- | --- |
| Answers from what it learned in training | Answers from your live data, read through tools |
| Can only describe how to do something | Can do it, when you ask and allow it |
| Guesses when it doesn't know | Looks it up, or says it can't |
| Lives in one window | Works inside the tools you connect it to |

The tools are what make an agent useful, and also what make it safe or unsafe. A good agent can only use the tools it's given, only with your permissions, and only does what you asked.

## What MCP is

The Model Context Protocol is an open standard, introduced by Anthropic in late 2024 and now supported by Claude, ChatGPT and many other AI apps and developer tools. It's often compared to a USB-C port for AI: instead of every AI app building its own connection to every tool, a tool offers one **MCP server**, and any AI app that speaks MCP can use it.

An MCP server tells the AI app three things:

1. **Which tools exist**, with a name, a description and the details each one needs.
2. **Which tools only read** and which change something, so the AI app can ask you before a change.
3. **Who you are**, through a sign-in you approve once, so every call runs as you, with your permissions.

For you, this means you can work with a tool from the chat you already use, without copying data between windows.

## What an API is, and how it differs

An API (application programming interface) is a set of fixed requests one program can send another: "list the candidates of this interview", "invite this email". Your developers write code that sends them. There's no AI involved: the same request always does the same thing, which is exactly what you want for automation that runs on its own.

| | AI agent (in the app) | MCP (in Claude or ChatGPT) | API |
| --- | --- | --- | --- |
| Who uses it | You, in prepza | You, in your AI chat | Your platform's code |
| How you ask | In your own words | In your own words | Fixed requests a developer writes |
| Who approves changes | You, on a card | You, in your AI app | Your code, as written |
| Best for | Quick questions and tasks | Mixing prepza with your other tools and files | Automation that runs without anyone watching |
| Signs in as | You | You | A company key |

Use an agent or MCP when a person is in the loop. Use the API when your own system should invite candidates and collect results by itself, for example from a careers site or an internal HR tool.

## What this is good for in hiring

Hiring has a lot of small, repetitive steps spread across tools. An agent is good at exactly those:

- **Questions about your pipeline.** "Which candidates for Senior Backend passed this week?", "Who hasn't started their interview yet?", "What's our average grade for the data analyst role?"
- **Setting things up.** "Create an interview from this job description", "Set the pass mark to 70%", "Give this candidate 50% extra time."
- **Bulk work.** "Invite these 12 people to the frontend interview", pasted straight from an email or a spreadsheet.
- **Combining sources.** In Claude or ChatGPT you can mix prepza with your other connected tools and files: compare a job description in your documents with the interview's topics, or draft a message to the shortlisted candidates.

What it should not do is make the hiring decision. A grade supports a person's judgment; it doesn't replace it. Ask the agent to sort, summarize and prepare, and keep the decision with a person. See [Is AI hiring legal in the EU?](/guides/is-ai-hiring-legal-in-the-eu) for why that matters legally, too.

## What to watch out for

Connecting an AI to your hiring data deserves the same care as giving a colleague access.

| Risk | What helps |
| --- | --- |
| The agent does something you didn't mean | Changes need your approval first, and it does only what you asked |
| It sees more than it should | It acts as you: it sees what you see, nothing more |
| Instructions hidden in data | Candidates' names, answers and documents are data, never instructions to follow |
| Secrets end up in a chat | API keys and passwords never go through the chat |
| Irreversible mistakes | Deleting an account or a company stays in the app, behind its own confirmation |
| Data leaves your tools | Data reaches the AI app you connect, under that app's terms: only connect apps your company allows |
| Runaway usage | Limits on how many actions run per hour |

Before connecting any AI app to work data, check your company's policy on AI tools, and tell candidates in your privacy notice which services process their data.

## Three ways to work with prepza beyond its pages

### 1. The built-in agent

Select **ask agent** in the header of any page. The agent knows your companies, interviews, candidates, credits and integrations, and how prepza works. It answers in your language, and you can type or speak.

- **It answers from your data**, with the same view you have: an admin sees what an admin sees, a viewer what a viewer sees.
- **It knows the page you're on.** Ask "What can I do on this page?" for that page's guide, or "Who's best here?" on an interview's candidates, and it answers about that interview without asking which.
- **It prepares changes, you confirm them.** Asked to invite candidates, it shows a card with exactly what will happen, such as "Invite 12 candidates to Backend developer". Nothing runs until you select confirm.
- **It shows its sources.** Under an answer you get the candidates or interviews it used and a link to the page they came from.
- **It stays on topic.** It answers about prepza and hiring with it, and declines the rest.

### 2. prepza in Claude or ChatGPT, through MCP

If your team already works in Claude or ChatGPT, you can bring prepza there. prepza's MCP server offers the same tools as the built-in agent.

**To connect:**

1. In prepza, open a company's **Integrations** tab and select **AI apps**. Copy the server address: `https://prepza.ai/mcp`.
2. **In Claude:** open Settings, then Connectors, and add a custom connector with that address. **In Claude Code:** run `claude mcp add --transport http prepza https://prepza.ai/mcp`. **In ChatGPT:** add it as a custom connector in its settings for apps and connectors.
3. Your AI app opens prepza's sign-in. Sign in, check which app is asking, and select **Allow**. To let it only read, turn off **Allow changes** first.

From then on, ask in your chat as you would ask a colleague: "In prepza, who are the top three candidates for Product designer?" Most AI apps ask you before a change and warn you before anything that can't be undone: prepza tells them which actions change or delete something.

**What stays the same as in the app:**

- **Your permissions.** It acts as you, in every company you're in, with your role in each.
- **Credits and limits.** Inviting a candidate costs the same as in the app, and the same email limits apply.
- **The record.** Everything an AI app does for you shows in the company's action log as done through an AI app, from approving topics and viewing results to giving extra time or revoking a candidate. The company's owner reads it on the company's **Action log** tab.
- **The company decides.** Owners and admins can stop AI apps from using a company's data with **Allow AI apps in this company** on its AI apps page.
- **What it can't do.** It can't see your password or API keys, and it can't delete your account or a company. Those stay in the app.

**To disconnect,** remove the connector in your AI app, or select **Disconnect** next to it under **AI apps** on the Integrations tab. It stops working at once.

**Other apps and your own agents.** The developer docs' [MCP tab](/api-docs?tab=mcp) has the steps for Gemini CLI, Cursor, VS Code and Le Chat, and complete example agents in Python and TypeScript. An agent that runs on a server, with no one there to approve a sign-in, uses a company API key with the **Use with AI agents (MCP)** permission: it works only in that company, and only with the tools the key's other permissions allow.

### 3. Your own platform, through the API

For automation without AI, prepza has an API, described in its [developer docs](/api-docs).

1. An owner or admin opens a company's **Integrations** tab, then **API**, and selects **New key**. Name it after the platform that will use it, choose when it expires, and tick only what it needs: a dashboard's key only reads, a careers site's key also invites. You can take permissions away later, never add them. The key is shown once; store it somewhere safe.
2. Your platform sends requests with that key: list the company's interviews, list or read candidates with their grade, whether they passed and their integrity signals, and invite a candidate.
3. Add a **web hook**: an address on your platform that prepza calls, signed, when a candidate starts, finishes, isn't reached, expires or is removed, and when an interview is ready, so you don't have to keep asking. The API page can send it a test event and shows its delivery log.

Each candidate comes with a link to their full results in prepza and, until they finish, their own invite link, so your platform can send it in its own message if you prefer. When your platform already knows who the candidate is, invite them without sign-in: prepza sends no emails, and the candidate takes the interview from the link without signing in to prepza, so send the link only to them. An invite can also bring the candidate back to your site with a button on the finished page, and set a light or dark theme in your company's colors. With prepza's SDK, your own page can show the interview itself. Bringing candidates back and showing the interview on your site need a verified company, and work only on its website domain.

The same rule holds as everywhere else: the grade supports a person's decision, so don't reject candidates automatically on it.

## Which one to use when

Start from who does the work and how often.

| Your situation | Use |
| --- | --- |
| You're in prepza and want a quick answer: who passed, who hasn't started, how many credits are left | The built-in agent |
| You want to set something up in a few words: an interview from a job description, a pass mark, extra time | The built-in agent |
| You already work in Claude or ChatGPT all day and want prepza there too | MCP |
| The task needs prepza plus something else: your documents, email drafts, another connected tool | MCP |
| A recruiter on the go wants to check the pipeline from the AI app on their phone | MCP |
| Your careers site or HR system should invite candidates by itself, with nobody clicking | The API |
| Results should land in your own database or dashboard as soon as candidates finish | The API, with a web hook |
| Your ATS is one prepza connects to (Workable, Greenhouse, Teamtailor, Recruitee, Breezy HR) | None of these: connect the ATS on the Integrations tab. See [How to connect skills tests to your ATS](/guides/ats-integration-skills-tests) |

A simple rule of thumb:

- **A person asks, and checks each change:** the agent in prepza, or MCP if that person lives in Claude or ChatGPT.
- **Software acts on its own, the same way every time:** the API.
- **Starting out:** try the built-in agent first. It needs no setup, and what you learn carries over to MCP.

They work together, too. A team can run invites from its HR system through the API, while recruiters ask the agent or their AI chat about the results.

## Getting good results

- **Name things.** "The Senior Backend interview" works better than "that interview".
- **Ask for one step at a time** when it matters. Check the result, then ask for the next.
- **Read the approval before you allow it.** It shows exactly what will run.
- **Ask where a number came from.** A good agent can point to the candidates or page behind it.
- **Keep decisions human.** Use the agent to find, sort and prepare; decide yourself.

## Pricing

The built-in agent, the MCP connection and the API are free to use. You pay only for candidates, the same as always: per candidate who answers at least one question, with no subscription. See [pricing](/pricing).

## Related reading

- [How to connect skills tests to your ATS](/guides/ats-integration-skills-tests)
- [Interviewing in the age of AI](/guides/interviewing-in-the-age-of-ai)
- [Is AI hiring legal in the EU?](/guides/is-ai-hiring-legal-in-the-eu)
