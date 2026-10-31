from site_content.constants.legal import COMPANY

# The privacy policy. Only this English text is binding; the site's translations are for reading.
# The help chat (the signed-out assistant) answers from it too.
PRIVACY_INTRO = f"This policy explains what personal data testee collects, why, how long we keep it, and the rights you have. testee is run by {COMPANY['name']} (registry code {COMPANY['registry_code']}), {COMPANY['address']}. testee.ai also shows this document in other languages; only this English version is binding, and where a translation differs, the English version applies."

PRIVACY_SECTIONS = [
    {
        "heading": "Who is responsible",
        "paragraphs": [
            f"For your own account and your company's account, {COMPANY['name']} is the controller of your data. Write to {COMPANY['email']} with any question or request.",
            "When a company invites you to an interview on testee, that company decides why and how your results are used and is the controller of them; we process them on its behalf. You can contact the company directly, or us, and we will pass your request on.",
        ],
    },
    {
        "heading": "What we collect",
        "items": [
            "Account: your name, email address, profile photo and account id, from the Google, LinkedIn or GitHub account you sign in with, and which of them are linked to your account.",
            "What you give us: job descriptions you paste and the interviews made from them, the notes you write on a company's interviews, the emails of the candidates you invite (and their names, if you give them or correct them), of the people you invite to your company's team and of the people you send a report to, and your ratings and reports of questions.",
            "The assistant: when you're signed in, what you write or say to it (a voice message is turned into text and never stored) and its answers, so you can come back to a chat. It doesn't keep what it read to answer you, such as candidates' results, apart from the records of AI calls below: when you open a chat again, it fetches them again with your current access. If you aren't signed in, your questions are used only to answer them and aren't stored, apart from the records of AI calls below. A message that contains a key, token or password is removed at once: it isn't stored or sent on.",
            "Companies: the company's name, logo and website, and the email domain it was verified with; when an owner or admin asks for verification, the email address on that domain they confirmed and the company name they sent for review.",
            "Practice: if you take free practice interviews, your answers, grades and how long each answer took. Only you see them, unless you turn on Open to offers.",
            "Open to offers: if you turn it on, the address of the LinkedIn profile you give, your name from the account you sign in with, when you turned it on, and a log of each time you turned it on or off, with the version of the wording you agreed to.",
            "Contact messages: the name, email address and message you send through the contact page.",
            "Interviews, if a company invites you: the email you were invited with, your answers, how long each answer took, when you left the interview page (and for how long), copied text or answered too fast to have read the question, whether your answer times and your right and wrong answers follow the questions' length and difficulty as other candidates' do, when you confirmed before starting that you'd answer on your own, any extra time the company gave you (no reason is recorded), and your ratings and reports of questions. You are told about this before you start. In an interview set to voice mode, what you say while answering is turned into text and matched to the options: one option you clearly name is saved as your answer at once, and you confirm a choice of several options first. What you say isn't recorded or stored, and your voice isn't analysed in any other way.",
            "Technical: error reports without your IP address or email, short-lived server logs needed to run and secure the service, and short-lived counters for rate limits, some keyed by your IP address.",
            "The \"I'm not a robot\" check: when you send the contact form, ask the help chat a first question, start an interview through a job ad's link, create your first company, or approve the topics of a company that hasn't paid yet, Cloudflare Turnstile looks at your browser (such as its type, how it behaves and the address it connects from) to tell a person from a script. We receive only whether the check passed.",
            "AI apps you connect: the app's name and the site it returns to, and when you connected it and last used it. Its access is kept only as a one-way hash.",
            "The terms you accepted: the version of the terms in force when you signed up, and when, as proof of what you agreed to. It's deleted with your account.",
            "Tools a company connects: the keys or tokens its owner or admin creates in its applicant tracking system (Workable, Greenhouse, Teamtailor, Recruitee or Breezy HR) or Slack, stored encrypted; a one-way hash of each testee API key and the addresses of its web hooks; and, from its applicant tracking system, the email, name and id of each candidate it sends to testee.",
            "Email settings: which optional emails you get, and a log of every change to them: which email, on or off, when, where (signing in, Settings, or an unsubscribe link or spam report) and which version of the checkboxes' wording you saw.",
            "Emails to company members: a record of the activity digests and reminders we sent you, and what each reminder was about, so none is sent twice.",
            "Emails to many users (notices of changes to our terms, important notices about the service, product updates, offers): whether each was sent to you, skipped or failed, and whether you unsubscribed from it or marked it as spam, so none is sent twice and we can see how each was received.",
            "Addresses we no longer email: if an email to an address bounces for good or is marked as spam, a one-way hash of the address, why and when. It can't be turned back into the email.",
            "Candidates who stop a company's emails: a one-way hash of their email address, with the company and, if they stopped only an interview's reminders, that invite. It can't be turned back into the email.",
            "Referrals: whose referral link you or your company came through, and whether it has been rewarded.",
            "Purchases: for each top-up, the company it was for, who bought it, what was bought, the total and currency, Paddle's transaction id and when. Paddle, not us, keeps the card and billing details.",
            "A company's action log: what its members do in it, such as inviting, viewing or removing a candidate, changing an interview or the team, topping up or connecting a tool, with who did it, when, and whether the assistant, an AI app or the API did it for them. The company's owner sees it. Candidates and members are named only while they're still in the company: the log keeps their ids, never their emails.",
            "AI usage and limits: for each use of AI, such as writing questions or the assistant's answer, what it was for, the model, its size and its cost, and the account and company it was for; and each time a limit refuses a request, which limit, when, and the account and company it refused. Never the text sent to the AI or its answer.",
            "Records of AI calls: what testee sends to the AI and what it answers each time it's used, such as writing questions from a job description, or the assistant's and the help chat's answers with what they read to answer (which can include candidates' results), and the votes on those answers. They're kept by Langfuse, below, only to monitor and improve the quality of the answers.",
            "Usage statistics: steps such as signing up, a company being created, a candidate invited or a top-up, with counts like a score or an amount. Your account id is replaced by a code made with a secret key we hold, so the statistics don't name you, but they are pseudonymous, not anonymous: with the key, the code matches your account id. A company's id is kept as it is. No names, emails or texts are included.",
        ],
    },
    {
        "heading": "Why we use it",
        "items": [
            "To provide testee: generating interviews, running them for invited candidates, showing companies the results and sending the emails you ask for (contract).",
            "Service emails, such as invites, reports, billing problems, changes to our terms and important notices about the service (a security incident, planned downtime or a change to how it works), which are always sent (contract).",
            "The activity digest and reminders about your companies, such as low credits or an interview with no candidates (our legitimate interest in helping you use testee). They are on until you turn them off.",
            "Product updates and news: for our own users who didn't tick \"Don't send me product updates and news\" the first time signing in offered it (article 13(2) of the ePrivacy Directive and § 103¹ of the Estonian Electronic Communications Act). You can stop them at any time, free of charge.",
            "Offers and promotions: only if you agree, by ticking the box when you sign in or in Settings (consent). You can withdraw it at any time.",
            "Choosing whom an email to many users goes to: whether your account is on a company's team (and whether as an owner or admin), has taken a company's interview or has used free practice, so a product update, an offer or an important notice can go only to those it concerns. Only that your account did so is used, never your answers, results or what a company holds about you (our legitimate interest in sending only relevant emails). Product updates and offers still go only to those who get them under the two points above.",
            "Remembering that a candidate stopped a company's emails, so testee doesn't email them for that company again (respecting their objection).",
            "To keep testee secure and working: preventing abuse, rate limits, error reports, and statistics that improve question quality (our legitimate interest).",
            "Question quality: we analyse how questions are answered and reported to find general, anonymised patterns of question quality that improve question generation for everyone; these patterns contain no personal data (our legitimate interest).",
            "Reuse of generated questions: questions testee generates may be reused in other customers' interviews and practice, without any personal data or detail that identifies a company or a person. A company can keep an interview's questions out of this in its settings.",
            "Records of AI calls let us monitor and improve the quality of the AI's questions and answers (our legitimate interest).",
            "Cost control and preventing abuse: the records of AI usage and of limits reached show what AI costs and who reaches which limit, so we can keep testee affordable and stop misuse (our legitimate interest).",
            "A company's action log lets its owner see who did what in the company, and our support check it when the company asks for help (the company's and our legitimate interest in accountability).",
            "Usage statistics show which parts of testee help people and which prices and limits work, so we can improve them (our legitimate interest).",
            "Purchase records, kept for bookkeeping as Estonian accounting law requires (legal obligation).",
            "Showing a company as verified, by checking its website against the email domains of its owners and admins (our legitimate interest).",
            "Open to offers: only if you turn it on (consent), companies hiring on testee see your name, your LinkedIn profile and your latest timed practice result on each subject you practised that one of their interviews covers at its level, so they can invite you to that interview. We don't rank or recommend you and make no decision about you: the company decides whom to invite. You can withdraw at any time in Settings, and you then disappear from every company's list at once. The log of your choices is kept as proof of your consent (our legal obligation to show it).",
            "Interview results, timings and integrity signals help the hiring company assess your answers fairly (the company's legitimate interest). The signals include patterns in your answers: times about the same on every question, or hard questions right while easy ones were wrong; with them, the company is shown questions to ask you about in a live interview. People at the company make the hiring decision; testee makes no decision about you on its own. You can ask the company for a person to review your result, and for an accommodation such as extra time before you start.",
        ],
    },
    {
        "heading": "Who we share it with",
        "paragraphs": [
            "We share data with the service providers that run testee for us, under agreements that protect it, and with Paddle, which sells the top-ups:",
        ],
        "items": [
            "Google (Firebase Authentication; Google LLC, United States, under the EU-US Data Privacy Framework): sign-in. LinkedIn and GitHub only confirm who you are when you sign in with them; we don't receive anything else from them.",
            "OpenAI: writing questions from the text you provide; the assistant's answers, from your questions and the data it reads with your access to answer them; turning voice messages into text; in voice mode, turning a candidate's spoken answer into text and matching it to the options (questions read aloud hold no personal data); and checking reported questions (only the reasons given, never the comments). We tell OpenAI not to store it: under its API terms it keeps this data for at most 30 days, only to check for abuse, and doesn't use it to train its models. (OpenAI Ireland Ltd, under our data processing agreement with it; it transfers the data to OpenAI in the United States under the European Commission's standard contractual clauses.)",
            "Resend: sending emails: invites and reminders to candidates, reports, emails to company members such as the activity digest, and contact messages (in the EU, Ireland).",
            "Google Workspace: our email inbox, which receives contact messages and the emails you send us (Google Ireland Ltd; mail may be stored outside the EU, under the EU-US Data Privacy Framework and standard contractual clauses).",
            "Sentry: error reports, with emails removed (in the EU).",
            "Langfuse (Langfuse GmbH, Germany, its EU cloud): records of AI calls (what is sent to the AI and its answers, which can include job descriptions, questions, chat messages and what the assistant read to answer them, and votes on the assistant's answers; in voice mode, only which options an answer matched, never its words), to monitor and improve the quality of answers (in the EU).",
            'Cloudflare (Turnstile; Cloudflare, Inc., United States, under the EU-US Data Privacy Framework): the "I\'m not a robot" check.',
            "Google Cloud, our hosting provider, which stores the data (in the EU, Belgium).",
            "Upstash: short-lived counters for rate limits and live updates (in the EU, Belgium).",
            "Companies, only if you turn on Open to offers: companies hiring on testee see what is described above. Each is responsible for how it uses what it sees. If one invites you, the invite goes to your account's email, and the company sees that email as it sees any candidate's.",
            "Paddle (Paddle.com Market Ltd, United Kingdom) isn't one of them: it sells the top-ups itself, as the merchant of record, and is the controller of the payment, tax and billing details it collects, under its own privacy policy. We pass it the email of the member buying, and it tells us what was bought and paid.",
        ],
    },
    {
        "heading": "Tools a company connects",
        "paragraphs": [
            "A company can connect its own tools to testee, and then we send them data on its instruction, as part of the service it asked for: its applicant tracking system (Workable, Greenhouse, Teamtailor, Recruitee or Breezy HR) receives your grade, whether it reached the passing grade, the integrity signals and a link to your results; a Slack channel it chose receives its notifications, such as that you finished and your grade; and its own systems, through testee's API or web hooks, receive your email, name, progress, grade, whether you reached the passing grade, the integrity signals and your invite link. The company chooses and controls these tools, which may be outside the EU, and is responsible for how they use your data.",
        ],
    },
    {
        "heading": "AI apps you connect",
        "paragraphs": [
            "You can connect an AI app of your own, such as Claude (by Anthropic) or ChatGPT (by OpenAI), to your testee account. Only when you do, and only for what you ask it, it reads and changes your companies' data with your access, including candidates' results, and that data reaches the app's provider under the app's own terms and privacy policy, not ours. You choose these apps and can disconnect one at any time on a company's Integrations tab; deleting your account disconnects them all. A company's owners and admins can stop AI apps from using that company's data.",
        ],
    },
    {
        "heading": "Emails and unsubscribing",
        "paragraphs": [
            "Service emails, such as invites, reports, billing problems, changes to our terms and important notices about the service, are always sent. You choose the others in Settings, under Emails: the activity digest, reminders, product updates and news, and offers and promotions. Every optional email has an unsubscribe link that works without signing in, and marking an optional email as spam turns it off too. If an email to you bounces for good, or you mark one of ours as spam, we stop sending product emails and notices to that address until you ask us to start again.",
            "Invites and reminders a company sends to candidates through testee have links to stop that company's emails, or that interview's reminders. testee then doesn't email that address for the company again, and the company sees the invite as not delivered.",
        ],
    },
    {
        "heading": "Transfers outside the EU",
        "paragraphs": [
            "Three of these providers handle data in the United States: Google, for sign-in, OpenAI, and Cloudflare, for the \"I'm not a robot\" check. These transfers are covered by the EU-US Data Privacy Framework or the European Commission's standard contractual clauses, as noted above. For people in the United Kingdom, the transfers to the United States rely on the UK Extension to the EU-US Data Privacy Framework (Google, Cloudflare) and on the standard contractual clauses with the UK International Data Transfer Addendum (OpenAI). Write to us for a copy of the safeguards that apply.",
        ],
    },
    {
        "heading": "How long we keep it",
        "items": [
            "Your account and everything in it: until you delete your account.",
            "Interview results, timings and integrity signals: 12 months after the invitation was last sent, then deleted automatically.",
            "Candidates an applicant tracking system sends: their email, name and id there, 12 months after they arrive.",
            "Notifications in the app, such as that a candidate finished: 90 days.",
            "AI apps you connect: until you disconnect them or delete your account; a connection unused for 90 days ends by itself.",
            "Your chats with the assistant: 90 days after their last message. You can delete a chat at any time, and they're deleted with your account or the company they're about.",
            "A company's action log: who did what, kept 12 months.",
            "Notes you write on a company's interviews: until you delete the note or the company deletes the interview or itself. They belong to the company, so they stay with it, without your name, when you leave it or delete your account.",
            "Records of AI usage and of limits reached: 13 months, without your account id once you delete your account.",
            "Practice rounds: until you delete your account.",
            "Open to offers: until you turn it off or delete your account, and at most a year after you last turned it on or saved your LinkedIn profile; the log of your choices, until you delete your account.",
            "A report emailed from testee: the PDF is kept only to send the email, and deleted at most 7 days later.",
            "Pasted job descriptions in our generation records: 90 days after the generation finishes. The interview made from them stays in the company's account until it's deleted.",
            "Your email settings and the log of their changes: until you delete your account.",
            "The record of digests and reminders sent to you: 30 days, or until you delete your account if that's sooner.",
            "The record of notices, product updates and offers sent to you: until you delete your account.",
            "An address we no longer email, as a hash: until you ask us to email it again, also after you delete your account, so it isn't emailed again.",
            "A candidate's request to stop a company's emails, as a hash of their email: until the company is deleted, even if the company erases the candidate.",
            "Contact messages: as long as we need them to answer you, at most 2 years.",
            "Error reports: up to 90 days.",
            "Records of AI calls at Langfuse: 30 days, then deleted automatically.",
            "Database backups: 14 days, then overwritten; anything deleted is gone from them by then.",
            "Usage statistics: 25 months, then deleted automatically.",
            "Purchase records: as long as accounting law requires (7 years in Estonia), without your account id once you delete your account.",
            "A one-way hash of your email after you delete your account, only so that signing up again doesn't repeat the welcome credits. It can't be turned back into your email.",
        ],
    },
    {
        "heading": "Your rights",
        "paragraphs": [
            'You can see, download and delete your data yourself: "Download my data" and "Delete account" are in Settings, in your account menu. Your data includes your answers and grades in companies\' interviews, but not which answers were right, as that would reveal the company\'s questions. You can also ask us to correct your data, to restrict or object to its use, or to move it to another service, at the address above.',
            "You can complain to the Estonian Data Protection Inspectorate (Andmekaitse Inspektsioon, www.aki.ee) or to the authority where you live; in the United Kingdom, the Information Commissioner's Office (ico.org.uk).",
        ],
    },
    {
        "heading": "If you live in the United States",
        "paragraphs": [
            'We collect the categories described above: identifiers (name, email, account id), professional information (interview and practice results), internet activity (page leaves, copies and answer times during a test) and, for companies, commercial information (purchases); from you, the company that invites you, its applicant tracking system and your sign-in provider; for the purposes above. We don\'t sell your personal information or share it for cross-context behavioural advertising, and we use no sensitive personal information to infer anything about you, so there is nothing to opt out of; a Global Privacy Control signal needs no action. You can ask to know, get a copy of, correct or delete your personal information ("Download my data" and "Delete account" in Settings, or write to us), also through an authorised agent, and we won\'t treat you differently for it. For a company\'s interview, the company decides and we pass your request on, as its service provider.',
        ],
    },
    {
        "heading": "Cookies and storage",
        "paragraphs": [
            "testee uses only the cookies and browser storage it needs to work or that remember your own choices. There are no advertising or analytics cookies.",
            "To keep you signed in: a cookie (testee_token, renewed every hour while you use testee, until you sign out) and the browser storage of our sign-in provider, Google Firebase. While you connect an AI app, a cookie (testee_connect) lasts the few minutes it takes.",
            "To remember your choices: your language (a cookie, testee_locale, for a year, set when you choose a language or open testee at a language's address), your light or dark theme, the width of the assistant's panel, how you last invited candidates, that you signed in on this browser before, the period you last chose for statistics, the notices about a changed legal document you closed, and your conversation with the assistant (until you sign in, only in this tab). They stay in your browser until you clear them.",
            "A referral link: only if you choose to keep it, a cookie (testee_ref) remembers the link you came through for 30 days, so the credits reach both companies.",
            'The "I\'m not a robot" check runs in a small frame from Cloudflare when a form needs it, and sets no tracking cookies.',
        ],
    },
    {
        "heading": "Children",
        "paragraphs": [
            "testee is not meant for anyone under 16.",
        ],
    },
    {
        "heading": "Changes",
        "paragraphs": [
            "We update this page when our practices change, and email you about a significant change at least 14 days before it applies. Every earlier version stays readable on this page.",
        ],
    },
    {
        "heading": "Contact us",
        "paragraphs": [
            f"Questions about this policy or your data: write to {COMPANY['email']}, or use the contact page linked at the bottom of every page.",
        ],
    },
]
