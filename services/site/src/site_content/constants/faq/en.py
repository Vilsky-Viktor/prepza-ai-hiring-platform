# The FAQ in en; the {placeholders} are filled in by helpers/help.py (faq_values) with
# billing's prices and the number of languages.
FAQ = [
    {
        "key": "what",
        "question": "What is prepza?",
        "answer": "A timed interview made from your job description, for any role. Use it to screen candidates before you meet them, or as a hiring step itself: either way, you see who really knows the job.",
    },
    {
        "key": "roles",
        "question": "Which roles can I hire for?",
        "answer": "Any role where knowledge matters: support, sales, finance, healthcare, trades, engineering, marketing and more. If you can describe the job, prepza can build an interview for it.",
    },
    {
        "key": "hiring",
        "question": "How does it work?",
        "answer": "Paste a job description on the home page, name your company and check the topics prepza proposes. Then invite candidates: type their emails, paste a list or upload a file. Candidates who haven't started after a few days get one reminder. Each candidate gets their own questions and a timer on each one, and you see their score and every answer as soon as they finish.",
    },
    {
        "key": "link",
        "question": "Can I put an interview in a job ad?",
        "answer": "Yes. Turn on the interview's shareable link on its settings tab and paste it into your ad. Anyone who opens it signs in and takes the interview, and each person is charged like an invited candidate. The link turns off when you mark the interview as hired.",
    },
    {
        "key": "preview",
        "question": "Can I try an interview before inviting anyone?",
        "answer": "Yes. Open your interview as a candidate from its page, free of charge: previews don't appear among your candidates or in question statistics. You can also take any of the free practice interviews.",
    },
    {
        "key": "cheating",
        "question": "Can candidates use AI or look up the answers?",
        "answer": "Every candidate gets their own random questions in their own order, with [a timer on each question](/guides/skills-test-timing-and-extra-time) that our server keeps, so there's little time to look answers up or ask an AI. The scorecard also shows when a candidate left the page, copied text, or answered too fast to have read the question. Once they finish, their page also points out answer patterns that relaying questions to an AI tends to leave, such as about the same time on every question or hard questions right while easy ones were wrong, and suggests questions they got right to ask about in a live interview. A pattern is a reason to ask, not proof. Before starting, each candidate also confirms they'll answer on their own, without AI tools or other people, and their scorecard shows it.",
    },
    {
        "key": "cost",
        "question": "How much does it cost?",
        "answer": "Generating interviews is free. Each candidate who answers at least one question costs {candidate} credits ({candidate_price}), and less with credits from larger top-ups, down to {cheapest_price}. Your first company gets {company} free credits, enough for its first {company_candidates} candidates. The [pricing page](/pricing) lists every price.",
    },
    {
        "key": "charged",
        "question": "When is a candidate charged?",
        "answer": "Once they've answered at least one question: when their interview ends (they finish it, or its time runs out while they're away), or when you revoke them. A question whose time ran out with no answer picked doesn't count. Their credits are set aside when you invite them, and come back if you revoke them before they answer anything, if they never start, or if their interview ends with nothing answered.",
    },
    {
        "key": "compare_hiring",
        "question": "How does the price compare with other assessment tools?",
        "answer": "Many assessment tools are sold as monthly or annual subscriptions, paid whether or not you test anyone. With prepza you pay only per candidate: {candidate} credits ({candidate_price}), with no contract, no seat fees and nothing to pay for generating an interview. A company inviting {example_candidates} candidates a month pays about {example_year_price} a year. If you test many candidates every month, a subscription can cost less, so compare with your own numbers.",
    },
    {
        "key": "expire",
        "question": "Do credits expire?",
        "answer": "No. Credits never expire, and there are no paid subscriptions. If you turn on the optional automatic top-up, Paddle saves your card as a {zero_price} subscription; you pay only for the top-ups it makes.",
    },
    {
        "key": "currency",
        "question": "Which currency do I pay in?",
        "answer": "Prices are in the local currency in Canada, Australia, Israel, Poland, Switzerland, Japan, South Korea, Taiwan, Hong Kong, Thailand, Singapore and India; in euros in the rest of the EU and in Iceland, Liechtenstein and Norway; in pounds in the UK; and in US dollars elsewhere. Your account and each company keep the currency of the country they were created in, wherever you travel: change yours in Settings, and a company's beside its Top up button (owners and admins). A company's top-ups, automatic ones too, are always charged in the company's currency.",
    },
    {
        "key": "refunds",
        "question": "Can I get a refund?",
        "answer": "Yes, for credits you bought in the last 14 days and haven't spent: through Paddle, or by writing to us. Free credits, such as the welcome gift, aren't refunded. The [terms](/terms) have the details.",
    },
    {
        "key": "scorecards",
        "question": "What do scorecards show?",
        "answer": 'Every answer, whether it was right and how long it took. A grade is the percentage of points earned: each question is worth one point, and a "select all that apply" question earns part of it for each right option ticked, and nothing if a wrong one is ticked. Grades show green or red against the passing grade you set for the interview. Scorecards also flag answers too fast to have been read, times the candidate left the page, and copy attempts.',
    },
    {
        "key": "reports",
        "question": "Can I share results with a hiring manager?",
        "answer": "Yes. Download a PDF report for one candidate or for all of an interview's candidates, email it straight from prepza, or send a short summary on WhatsApp, Telegram, Viber or LINE.",
    },
    {
        "key": "action_log",
        "question": "Can I see who did what in my company?",
        "answer": "Yes, if you own the company. Its Action log tab lists everything its members did, newest first: inviting or removing candidates, viewing results, changing interviews, the team, billing and integrations, with who did it, when, and whether the assistant, an AI app or the API did it for them. You can filter it by member, kind of action and dates. Actions are kept for 12 months.",
    },
    {
        "key": "notes",
        "question": "Can my team keep notes on an interview?",
        "answer": "Yes. Each interview has a Notes tab where your team writes plain-text notes about the hiring round, such as whom to call next or, for an agency, which client the interview is for. Every member can write notes, viewers too, and edit their own; the author, owners and admins can delete one. Owners and admins can pin one note, which then shows under the interview's name. Candidates never see notes.",
    },
    {
        "key": "integrations",
        "question": "Does prepza work with my ATS or other tools?",
        "answer": "Yes, at no extra cost. Connect Workable, Greenhouse, Teamtailor, Recruitee or Breezy HR on your company's Integrations tab: candidates you move to a stage get the interview, and their results go back to the ATS ([how to connect skills tests to your ATS](/guides/ats-integration-skills-tests)). Slack can post your company's notifications to a channel, and the API lets your own platform create interviews, invite and manage candidates and receive their results, with each API key limited to what you tick for it; see the [API docs](/api-docs).",
    },
    {
        "key": "ai_apps",
        "question": "Can I use prepza from Claude, ChatGPT or my own AI agent?",
        "answer": "Yes. Add prepza to Claude or ChatGPT as a connector (the steps are on your company's Integrations tab) and allow it on prepza. The app then works with your companies, interviews and candidates' results as you, with your permissions; most apps ask you before they change anything. Deleting your account or a company is done only in prepza. What the app reads reaches its provider under that app's terms. You can disconnect it at any time on the same tab. Other AI apps and agents you build yourself connect too: the developer docs' [MCP tab](/api-docs?tab=mcp) has the steps and example agents, and an agent on a server can sign in with an API key that has the AI agents permission. The [guide to AI agents, MCP and APIs](/guides/ai-agents-mcp-and-api) explains what each is for.",
    },
    {
        "key": "candidates",
        "question": "What do candidates see?",
        "answer": "Your company's name and logo, in your company's colors and fonts (set on its brand tab), what to expect before they start, then one timed question at a time. They never see their score or whether an answer was right.",
    },
    {
        "key": "verified",
        "question": "What does the verified check mean?",
        "answer": "That an owner or admin of the company signed in with a work email on the company's website, such as you@acme.com, and our team then reviewed the company. Add the website with Verify in your company's header; free email services don't count. While the review is pending, your team sees a clock next to the name, and renaming the company sends it for review again. The check shows next to your company's name, including in invites.",
    },
    {
        "key": "languages",
        "question": "Which languages are supported?",
        "answer": "{count} languages, for the site, the interviews and the emails. Choose the language an interview is written in, whatever language the job description is in.",
    },
    {
        "key": "privacy",
        "question": "What happens to job descriptions and answers?",
        "answer": "Job descriptions are used to build your company's interviews, and candidates' answers to score them for your company. The questions prepza generates may also be reused in other companies' interviews and practice, without anything that identifies you, your company or anyone else; you can keep an interview's questions out of this in its settings. prepza also learns general, anonymised patterns of question quality from how questions are answered, to improve how questions are generated. The [privacy policy](/privacy) explains what we keep, for how long, and everyone's rights.",
    },
    {
        "key": "eu_ai_law",
        "question": "Is it legal to use AI to screen candidates in the EU?",
        "answer": "Yes, with rules. Under the EU AI Act, tools that score candidates are very likely high-risk, with duties from 2 December 2027, and the GDPR already applies: a person makes the hiring decision, candidates are told AI is used, and records are kept. prepza works that way: AI writes the questions, people at your company review the results and decide, and candidates are told before they start. This isn't legal advice; [Is AI hiring legal in the EU?](/guides/is-ai-hiring-legal-in-the-eu) explains the rules and the dates.",
    },
    {
        "key": "emails",
        "question": "Which emails does prepza send, and how do I stop them?",
        "answer": "Service emails, such as invites, reports, billing problems and changes to our terms, are always sent. The rest, such as the daily activity digest, reminders and product updates, you choose in Settings, under Emails, or stop with the Unsubscribe link in each email. Candidates can stop your company's emails, or an interview's reminders, with the links in their invites and reminders. prepza's news shows in your notifications, the bell at the top; the major news also comes by email as a product update, only while that setting is on.",
    },
    {
        "key": "delete",
        "question": "Can I delete my account?",
        "answer": "Yes, in Settings. Your account and your data are deleted, and you can download a copy of your data first.",
    },
    {
        "key": "report",
        "question": "How do I report a problem?",
        "answer": "Write to us on the [contact page](/contact) and paste the ID of what it's about: \"copy id\" is under the name of a company, an interview or a candidate, and your account's is in your account menu and in Settings. With the ID we find it at once.",
    },
]
