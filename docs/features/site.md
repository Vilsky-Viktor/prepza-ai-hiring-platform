# Public site

The pages anyone can open without signing in, and how search engines see them. Every public page also has an address in each language (see [Languages](languages.md#language-addresses)).

The site follows the device's light or dark setting until a visitor picks a theme (`providers/theme-provider.tsx`). The header's theme buttons (in the account menu once signed in, not on phones) offer system, light and dark; "system" follows the device's light or dark setting, and the choice is kept in the browser (`theme` in local storage). A company's interview pages show the theme the link, the API or the SDK asks for, else the candidate's own (their device's setting unless they picked another); the PDF reports and the emails are always light.

- [Home page](#home-page)
- [Skills tests by role](#skills-tests-by-role)
- [Articles](#articles)
- [FAQ and help chat](#faq-and-help-chat)
- [Legal pages](#legal-pages)
- [Documents for companies](#documents-for-companies)
- [Contact us](#contact-us)
- [News](#news)
- [About us and the footer](#about-us-and-the-footer)
- [Search engines](#search-engines)

## Home page

The first screen: "Test everyone. Hire the best.", what prepza does and its price per candidate, each sentence on a line of its own, an info button that explains in a dialog how prepza works and a play icon under it (named in its tooltip, with a blue ring pulsing out of it, left out with reduced motion) that plays prepza's video in a window on the page (YouTube's no-cookie player, loaded only when the window opens): in the margin on the title's start side on wide screens, each with a thin line drawn out from under it and rising at an angle, "how it works" and "watch video" written along it; side by side above the title, without the lines, on narrower ones; then the box to paste a job description. From tablets up, four thin wires run from the window's edges into the box and out of it, with candidates moving along them. Under the box, a short line of facts: any job, the number of languages, how long an interview takes to be ready, and no subscription. At the bottom of the first screen, two blue chevrons fading down one after the other lead on to how it works. Submitting the box:

1. signs you in if needed,
2. asks, in a window over the box, which company the interview is for (the first one chosen at first; or its name, for a first company), Cancel closing it with the description kept,
3. starts the generation.

Below, the page follows a company's hiring, one section per screen, each with a short title, one sentence and a live picture that plays while it's on screen:

- **Create an interview in minutes:** one frame, the screens taking each other's place as the app's real screens: a job description pasted into the home page's box from the right-click menu and sent, and the window that opens over the box asking which company it's for, the user's company (Globex) chosen, then a new company picked, named Acme and continued; the AI's loading mark while the topics come; the topics (for an AI Engineer) adjusted, one edited with a subtopic added and one added by asking the AI, then approved; their questions written, then the finished interview, the questions each candidate gets changed on two topics, and the invite dialog (its tabs, without the mode switch) sending a candidate an invite. A numbered pill on the frame's top edge names the step shown ("1. Paste your description", "2. Adjust the topics", "3. Your interview is ready"). Under it a line of facts: that no subject expert is needed, how many questions are generated per topic (`INTERVIEW_QUESTIONS_PER_TOPIC` from the Controls tab, read from generation's public `GET /api/generate/sizes`; left out when generation doesn't answer), and that ready-made templates are available.
- **Invite candidates from everywhere:** the interview in the middle, wired to every way candidates come in: your ATS, email invites, bulk imports, a share link in a job ad, the API, the embedded SDK, Mira and AI apps over MCP, each a card with its icon or logos in a tile and, from laptops up, a few words on what it does, with candidates counted in as they arrive; a source above or below the interview and close to its side turns down (or up) into it, so no wires cross. Under the interview, Slack ("updates in your channel"), with a bell running along its wire for the notifications. Under the picture, "Automate hiring with" and the developer docs button (`/api-docs`). On phones the ways in sit in a row above the interview and a row below it, with Slack under them, without wires.
- **What candidates see:** a Click/Voice switch above the picture plays the interview in either mode, and a visitor can switch to either: in click mode the start page in the company's brand with its rules, the pledge ticked and a question answered with a tap and Next; in voice mode the start page, the browser's microphone prompt allowed, and Mira reading the question, hearing the answer, picking it and moving on. Under it a line of facts: click and voice modes, works on a phone, the time shown up front and extra time for those in need.
- **See who's best, share it in seconds:** the interview's candidates as the real list, with the search, status filter and sort above it and each row's integrity signals; their PDF downloaded and emailed to the hiring manager; the best candidate's page, scrolled down and up, shared to WhatsApp as a text summary with a line typed and sent, then the same for a candidate caught cheating; a note posted on the interview's notes (the tabs' counts: 10 topics, 73 candidates, 15 notes); last, the company's Slack channel, with its side menu, where prepza posts each "finished" message with an "Open in prepza" button (the only kind of this flow Slack gets). The frame keeps one size as the screens change. Under it a line of facts: interview notes, PDF reports, summaries via messengers and Slack notifications; then "Create an interview", which goes back up to the job description box, ready to type, and beside it "Report samples", which downloads `prepza-report-samples.zip`: the report of all candidates and one candidate's report as real PDFs, from made-up data ([Reports](candidates.md#reports)). On phones the two buttons stack.
- **Just ask Mira:** the assistant's panel, titled "Mira · AI assistant" and opening with Mira's greeting, answering how many candidates passed, how to give extra time (from a guide) and inviting a candidate once confirmed, beside what it does: info, help and actions.
- **Trust, quality and compliance:** the loop that keeps questions good: five steps of one size spaced evenly round an ellipse filled with a fine net, a pulsing brain in its middle (generated with its right answer and convincing wrong ones, checked blind by a second AI, answered and rated by candidates, flagged, rewritten), a question running round and lighting each step in turn while it's on screen, all of it still with reduced motion. Under it, four columns split by thin lines (one under another on phones): a person decides, fair to every candidate, built for compliance (with a link to the documents) and every action on record.
- **Better than phone screens, cheaper than subscriptions:** phone screens, testing tools and prepza side by side, by how the questions are made, your time and what you pay, with prepza's price range per candidate and a link to the comparisons with other tools.
- **Everything is free, pay per candidate:** a receipt for a whole interview where every step costs nothing and only the candidates who answered are paid for, at the top-up with the lowest price per candidate; beside it the free candidates to start, every top-up with its price per candidate (the receipt's marked), "Create an interview" and "See pricing", and the small print (no subscription, unanswered invites cost nothing, credits never expire, unused paid credits refundable). The pricing page, the top-up dialog and the automatic top-up's dialog say the same in a sentence: prices don't include VAT or sales tax, which Paddle adds at checkout.
- **The closing screen:** "Create your first interview. It's free." with "Create an interview" and the free candidates, then "More questions?" with buttons to ask Mira, the demo videos on YouTube, the FAQ and the guides.

Prices, the price range and the free candidates come from billing's catalog, so they follow any change, in the visitor's currency (their country's: see [Currencies](billing.md#currencies)), or a signed-in person's own (see [Currencies](billing.md#currencies)). The hero's second line ("Just $2 – $5 per candidate.") and the page descriptions name that range, written as each language writes a price range, and leave the price out when billing doesn't answer; without the catalog the page shows without the comparison and the pricing sections. Nothing in the pictures is real data. Signed-in users see the landing page too. On phones the animated pictures of creating an interview, what candidates see, the reports, Mira's chat and the quality loop are left out: their sections show their steps as cards instead (the three steps; click mode and voice mode; the PDF, sharing via messengers or email, and team notes and Slack; Mira's info, help and actions; the loop's five steps), each card the screen's full width with square corners and a gap between them, and the invite picture shows its cards without wires. The facts under each section stay, one a row, each after a blue dot. A picture plays once 40% of it is on screen, or, for one taller than that, once it fills 40% of the screen; scrolling within it doesn't start it again. With reduced motion every picture shows a still, complete frame (in the create section, the finished interview).

## Skills tests by role

`/tests` and `/tests/<slug>`: a page per template, for companies hiring for the role. It shows:

- what the test covers,
- the way to create a test,
- up to 5 of its practice questions with answers as examples, and a link to free practice,
- "questions companies ask": the FAQ's answers on cost, charging, cheating, what candidates see and languages. It has no FAQ structured data; `/faq` carries that.

Addresses use the template's slug (see [Templates and practice](templates-and-practice.md#slugs)); an old address by id moves there for good.

A role page, like the template's free practice page, is in English and in its template's language only. For a German template, that's `/de/tests/<slug>` and `/de/practice/<slug>`, with hreflang between the two. Its address in any other language isn't found.

## Articles

The articles are `/pre-employment-testing`, `/ai-interviews`, `/compare` and its pages, and `/guides` and its pages.

- They are Markdown in `frontend/content/` (`pages/`, `compare/`, `guides/`).
- Each has a short frontmatter: `title`, `seoTitle` (at most 60 characters), `description` (at most 155), `updated`; the body starts with `# <title>`. `tests/lib/content-front-matter.test.ts` checks every file in every folder and language.
- `lib/content.ts` and `features/content/components/` show them, in a centred reading column (`max-w-5xl`) with a back arrow beside the title to the article's section (home for a page without one) and the updated date in italics.
- A new file is a new page, in its hub and the sitemap.
- The guides (`guides/` and each language's) are also what the assistant reads for hiring advice: site serves them from the same files (`GET /api/site/help/guides`, the list by title, and `GET /api/site/help/guides/{slug}`, one with its Markdown, in the page's language, English until translated). Its image copies `frontend/content` to the same place relative to its code as in the repo, the local stack mounts it, and CI rebuilds site when a guide changes, so there's one copy of each article.

**Translations** live in `content/<language>/<folder>/`, under the same file name.

- A page shows its translation in the interface's language.
- Where there is none, it shows English, with a note.
- It names only its real translations, for hreflang and in the sitemap.

**Comparisons** name no competitor prices and say where each tool fits better; prepza is presented as complementary.

## FAQ and help chat

`/faq` has the common questions, in the interface language, with today's prices; its intro points to Mira, the AI assistant ("ask Mira" in the header) for anything else. Without prices (billing not answering), site refuses the FAQ (503) instead of building it with blanks: the site keeps showing the last good page, a role page leaves its FAQ section out, and the help chat answers without prices.

The questions are in `services/site/src/site_content/constants/faq/<language>.py`; a question not translated yet shows in English. An answer is plain text that may link to the site's own pages as `[text](/path)` (a guide, pricing, the API docs, ...): the page shows it as a link that opens in the same tab, in the address's language (`components/common/faq-list.tsx`, `FAQ_MARKDOWN` in `lib/markdown.ts`). Only a path on the site becomes a link; any other target stays its text, and the rest of the answer is shown as text. Every language links the same pages as English, in the same order (`tests/unit/test_faq.py`). The FAQ's structured data has each answer as plain text, its links as their text; the help chat and the assistant read the answers with their links as written.

The help chat (the assistant's `POST /api/assistant/help/chat`) answers signed-out visitors in the [assistant's panel](assistant.md#the-panel).:

- It answers only from the platform guide, the FAQ, the prices, the terms and the privacy policy, and keeps to prepza and hiring with it, like the assistant (`prepza_common.ai.scope.SCOPE_RULE`). Site owns that knowledge and sends it to the assistant for each question (`GET /internal/help/knowledge?country=&page=`, with a service token; the platform guide is cached per language and country). When site can't send it, or the model fails, the visitor gets the usual "Couldn't get a reply right now" error, and only the error's type is logged.
- It answers in the language code chooses: the question's own when it clearly shows one (its script, or at least two of a Latin-script language's common chat words, the assistant's `constants/chat_words.py`), else the page's; the model never guesses it. Each of the visitor's messages reaches the model inside `<visitor_message>`, read as data, and a conversation's answers share one Langfuse session (the page sends the chat's own id).
- Each question carries the key of the page it's asked on: the chat reads that page's guide, so "this page" and "here" mean it (see [page guides](companies.md#page-guides)). Every page with the panel has a guide, the public ones (pricing, practice, news, the articles, the FAQ, the documents) too; site serves them at `GET /api/site/help/pages/{key}`, which the info buttons read.
- A visitor shows they're a person ([the "I'm not a robot" check](../architecture.md#the-im-not-a-robot-check)) until their conversation has a reply.
- An answer's tokens count against the day's budget however it ends: estimated (about 4 characters each) when the model was cut short and reported none.
- Nothing of the conversation is stored: the panel sends it whole each time. Each reply ends with its signature (`{"done": true, "signature"}`, an HMAC of its text with the service's secret), which the panel sends back with it; the model reads every question but only the replies the chat signed, so a reply the page made up can't steer it, and only a signed reply spares the check.
- Each reply's last event also names the answer for a vote on it: `"answer": {"id", "trace_id", "signature"}` (a new id, its Langfuse trace when Langfuse is set up, and an HMAC of both). A thumbs up or down under it goes to `PUT /api/assistant/help/answers/{id}/vote` (`{"trace_id", "signature", "value": 1 | -1 | null}`, public): a wrong signature is refused ("There's no such answer."), so only the page that got the answer votes on it. The assistant keeps only the vote, by the answer's id, with its trace (its `help_votes` table; no text, question or voter), deletes it when cleared, and sends it on to Langfuse like the assistant's ([Votes in Langfuse](assistant.md#votes-in-langfuse)).
- A conversation with a secret in it (a key, a token, a password) is answered at once with a fixed reply, before the limits or the model, and nothing of it is used; see [the assistant's secrets](assistant.md#secrets-pasted-into-the-chat).
- A visitor asking to sign in or sign up, or to do something that needs an account (create a company, …), gets a sign-in card in the panel (the site's own sign-in buttons, the way they named first): the model starts its reply with a `[[sign_in:<provider>]]` marker, which the service turns into a `{"block": {"kind": "sign_in", "provider"}}` event.
- The same knowledge, with the FAQ in the page's language, is served as text at `GET /api/site/help/guide` (public, kept for 5 minutes per language); the in-app assistant reads it to answer questions about prepza.

Every limit but an answer's length and Cloud Armor's is one of `prepza_common.limits.limit_list`'s: it starts at its default, and a superadmin changes it in the admin zone's Controls tab (see [Admin zone](admin-zone.md#limits)).

| Limit | Where it's set | Default |
|---|---|---|
| Messages an hour per account | `HELP_USER_LIMIT` | 30 |
| Questions an hour per address | `HELP_IP_LIMIT` | 60 |
| Questions a day in all | `HELP_DAILY_LIMIT` | 5,000 |
| An answer's length, in tokens | `HELP_MAX_OUTPUT_TOKENS` constant | 1,500 |
| Tokens a day in all (input and output, counted after each answer; a started answer finishes) | `HELP_TOKENS_PER_DAY` | 50,000,000 |
| AI spend a day of unpaid companies and people without a company, the help chat's visitors included (503 until midnight UTC once reached) | `AI_SPEND_UNPAID_DAY` | $15 |
| Questions per 10 minutes per IP, at the edge (Google Cloud only) | Cloud Armor (Terraform) | 20 |

The chat's replies stream within the assistant's turns at once (`TURNS_AT_ONCE`, see [A conversation](assistant.md#a-conversation)); the model gets 1 retry and 25 seconds.

Each answer is recorded with its tokens and cost as a `help_chat` AI call (see [Credits and payments](billing.md#ai-usage-and-limit-hits)).

The chat's model is the assistant's `HELP_MODEL` setting (see [Generation](../generation.md#models) and [the assistant's settings](assistant.md#settings)).

## Legal pages

- The privacy policy, terms and data processing agreement are served by the site service (`GET /help/legal/{terms|privacy|dpa}?version=&language=`). The help chat answers from the English texts.
- **Languages:** each version is written in English, the binding text (each document's intro says so), and translated into the other 22 languages. A page shows its language's translation, saying it's a translation with a link to the English (`?language=en`); Arabic, Hebrew and Persian read right to left. Translations sit next to the English copy, at `src/rounds/legal_versions/<document>/<version>/<language>.json` in rounds, and a test requires every language for each current version, with the English's sections, paragraphs and items, and its addresses, links, numbers and dates. An older version without translations shows in English, saying so.
- **Versions:** each document's version is the day it applies from (`LEGAL_VERSIONS` in `prepza_common.config.constants`), and may come after the day it's published. Each page says "In force since …", or "Applies from …" with a link to the version in force now. Every published version stays readable (`/terms?version=<date>`, which says it was replaced), listed under **All versions**. Site keeps a copy of each in `src/site_content/legal_versions/<document>/<version>.json`, the current one too, and a test fails when a text changes without a new version: give it one, then run `python -m site_content.legal_archive` in site. Site decides which version applies today and whether the one shown is in force, upcoming or replaced.
- **Acceptance:** signing up accepts the terms in force (the sign-in says so, and that the privacy policy was read), and accounts keeps that version and when (`terms_acceptances`; in the data export, deleted with the account). A company keeps the DPA version in force when it was made (`companies.dpa_version`), which its owner accepted with the terms. A later version applies after its notice; the terms say that using prepza after that day accepts it.
- **Notices:** a significant change is emailed at least 14 days before it applies, from the admin zone (see [Legal notices](admin-zone.md#legal-notices)). It goes in the bell too, and until it applies a thin banner above every page tells signed-in users from when, with a link to it; closing it keeps it closed in that browser for that version (see [Notifications](notifications.md#legal-notices)).
- They sit in the articles' centred reading column, with a back arrow home beside the title, as do the about and accessibility pages.
- The contact address in them, hello@prepza.ai, is put together in the browser, so the page's HTML doesn't hold it for bots to collect.

## Documents for companies

The `/documents` page ("legal docs" in the footer) offers companies:

- instructions for use, as a PDF,
- the data processing agreement, as a PDF,
- candidate notice and DPIA templates, as editable Word files.

Their sources are the Markdown files in `frontend/content/documents`, in English only, like the legal pages. The DPA's text must match `services/site/src/site_content/constants/dpa.py`.

After changing one, rebuild the files in `frontend/public/documents` and commit them:

```bash
./scripts/documents/build.sh   # needs uv (for pandoc) and Docker (Chromium prints the PDFs)
```

## Developer docs

The `/api-docs` page ("developer docs" in the footer) is the public API's reference, in English only, like the legal pages. It reads the API's OpenAPI description on each request (`lib/openapi.ts`, `features/api-docs/components/`) and shows it in five tabs in a side menu, as on a company's pages (`?tab=`, `config/api-docs.ts`), the description split at its `# ` titles, except MCP's:

- **API** (the page's own address): getting a key, authentication, limits, errors, sending candidates from your own platform (any https `return_url`), allowed IPs, then the base URL and each route with its parameters, body, result and errors;
- **web hooks**: signatures and delivery, then the `candidate.finished` event;
- **SDK**: embedding the interview with the hosted script, with a code example, and the allowed domains that may embed it;
- **MCP**: connecting AI apps and one's own agents to prepza's MCP server, in pages of its own listed under it in the menu (`?tab=mcp&page=<id>`): an overview, a page per AI app, the server's tools, and agent frameworks with example agents in Python and TypeScript (its own English text in `config/mcp-docs.ts` and `content/mcp/`; see [AI apps over MCP](mcp.md#connecting));
- **objects**: what the routes and the web hook return; a type anywhere links to its object here.

The description's text may hold bold, inline code, links (`[text](/api-docs?tab=sdk)`: the API tab links its mentions of the web hook and of embedding to their tabs) and code blocks, each with its language ("```python"); code blocks that follow each other are one example in several languages, such as the routes' examples in curl, Python and JavaScript (`src/api/constants/docs.py` in the api service). See [Public API](api.md).

### Code

Code anywhere on the site shows in one editor (`components/common/code-editor.tsx`): a header with its language and a copy button, then numbered lines in the language's colors (shiki's GitHub themes, light and dark; plain for a language shiki doesn't know). The site's own code (articles, the developer docs, the home page's demo question, a role page's sample questions) is colored on the server (`components/common/highlighted-code.tsx`, `lib/code-tokens.ts`), so those pages never load shiki; code that arrives in the browser (the assistant's answers, interviews, practice) is colored there once shiki loads, plain until then. An example in several languages gets a language menu in the header instead, and picking one switches every editor on the page that has it (kept while the tab stays open, `lib/code-language.ts`). The developer docs, the articles and the assistant's answers (Markdown code blocks, `components/common/markdown-code.tsx`) use it, and so does a question's example in interviews and practice, without the header (`lib/question-text.ts` reads the block's language from its fence). The code itself is a named region that takes keyboard focus (with a focus ring inside its box), so code wider than its box scrolls with the arrow keys.

## Contact us

`/contact` is a form with a name, an email and a message, named by their placeholders (and `aria-label`s, for screen readers) without visible labels. Beside it from laptops up (above it on narrower screens), two cards: what to write about, and the company that runs prepza as labelled rows (name, registry code, address, and the email as a link).

- The site service keeps the message as a `contact.sent` event until it's published, and a week after; notifications emails it to hello@prepza.ai (`CONTACT_EMAIL`). A visitor who later deletes or downloads their account with the same email gets those still kept deleted or in the download. The form posts to site's `POST /api/site/help/contact`.
- The visitor's address is the reply-to, so answering the email answers them.
- The sender shows they're a person first ([the "I'm not a robot" check](../architecture.md#the-im-not-a-robot-check)).
- At most 5 messages a day per address (`CONTACT_IP_LIMIT`) and 200 a day in all (`CONTACT_DAILY_LIMIT`) by default; both are edited in the admin zone's Controls tab.

### IDs to quote

So support finds what a message is about at once, the page asks visitors to paste the ID of what they write about. Each one has a "copy id" button (`components/common/entity-id.tsx`) that copies its ID and shows a check mark for 3 seconds:

- a company's, under its name in the company's header;
- an interview's, under its title, beside its status (also while it generates, or after it failed);
- a candidate's invite, on the line under their email;
- the account's (the Firebase uid), as a small button under the email in the account menu, and as a button in Settings, under "Your account".

The FAQ ("How do I report a problem?") and the help chat and assistant's guide say the same. An email shown large (a candidate's page, the candidate, team and credits-held lists, the interview report) breaks before its `@` when it doesn't fit (`components/common/wrapped-email.tsx`), so it never runs off a phone's screen.

## News

`/news` ("prepza news.") lists prepza's posts newest first, one after another: title (ending with the blue dot, like the site's headings), date and text. No pictures, links or detail pages; the text is plain, with its line breaks. Superadmins write them in the [admin zone](admin-zone.md#news).

- Posts are written in English and translated into every other language after they're saved. Each language's page (`/de/news`, …) shows its translation, or the English post while there's none.
- The first page is rendered on the server; the next loads when you scroll near the end (site's public `GET /api/site/news?offset=&limit=`, in the `Accept-Language` language, no sign-in).
- Posts are read fresh on every request, not through the public data cache, so a new, changed or deleted post shows at once (`lib/news-posts.ts`).
- **In the bell:** each post reaches every signed-in user's bell, named in their language, opening it here; deleting the post takes it back (see [Notifications](notifications.md#the-bell)). News isn't emailed by itself: a superadmin can send a post as a product update to those who chose them.
- **Search engines:** its own title and meta description in each language, canonical and hreflang addresses for every language, the link-preview picture, and structured data: a `Blog` with the page's posts as `BlogPosting`s by prepza (`newsData` in `lib/structured-data.ts`). The sitemap lists it in every language, dated by its newest post.
- **RSS:** `/news/rss.xml` (and `/de/news/rss.xml`, … in each language, with the same translations) is an RSS 2.0 feed of the newest 50 posts: each with its title, its text as plain text, its day and its id as the guid, linking to its place on that language's news page (`#<id>`). The page names it in its head and links it with the large RSS icon on the right of its title. It isn't in the sitemap.

## About us and the footer

`/about` explains why prepza exists for companies, free practice for people preparing, and its solo founder.

`/accessibility` is the accessibility statement (the EU Accessibility Act; candidates are consumers): the WCAG 2.2 AA aim, what prepza does (themes, brand colors held to WCAG contrast, 23 languages with right-to-left, phone layouts, text-only questions, extra time a company gives, and the keyboard: a "Skip to content" link first on every page, tabs moved with the arrow keys, form errors announced), what falls short (timed questions, no independent audit yet, Paddle's and Cloudflare's parts), where to write (answered within 14 days) and the Estonian authority (TTJA), with the day it was last reviewed (`config/accessibility.ts`). It's in every language.

The footer names the company that runs prepza ("© <year> Arcolabs OÜ"); the contact page gives its registry code, address and email, every email ends with its name and address, and the home page's structured data has them too (all from `OPERATOR` in `prepza_common.config.constants`, mirrored in `frontend/src/config/operator.ts`). The footer has the social icons and "ask Mira", which opens the assistant, and its links in three columns: the product (skills tests, pre-employment testing, AI interviews, free practice, comparisons), resources (guides, FAQ, docs, API docs, news) and the company (About us, Contact us, privacy, terms, accessibility). On phones everything is centered, with the links in one column. Pricing is in the header's menu, not in the footer.

While a company's page loads its data (a service waking up can take a few seconds), the header and footer stay and the page's place shows a spinner (`app/companies/loading.tsx`, the one link pages show while loading). Only these signed-in pages have it: a loading state streams the page, so one of them that isn't found answers 200, which their `noindex` makes harmless, while public pages and the admin zone keep a real 404.

Corners are rounded the same everywhere, as the side menu's items are (`rounded-xl`): cards, lists, dialogs, menus, tooltips, fields and buttons; something set close inside one of them (a button in a field, a menu's item) is a step less rounded (`rounded-lg`), so the corners nest. Only avatars (except the account's in the header), dots, progress bars, sliders, switches, chips and a field's raised name are round. A field shows its name inside it: where the value goes while it's empty, and as a small pill on its top edge once it's focused or filled; a unit (s, px) sits inside the field at its end.

A search over a list (a company's interviews, an interview's candidates, the templates and the practice tests, the admin zone's support search) joins it as one block: the search on top, rounded at the top, and the list, or its empty state, straight under it, rounded at the bottom, the same width and inside one border, with a single line between them (`components/common/searched-list.tsx`).

On phones dialogs and menus span the screen's width, with square corners. A dialog's buttons stay in sight at its bottom edge, with only its body scrolling, and help dialogs fill the screen. Lists, search boxes and gray panels reach the screen's edges, a page's main button ("new company", "new interview", "add member") takes its own full-width line under the title, and rows put their numbers and buttons under their title. On touch screens the keyboard hints ("⌘/Ctrl + Enter to send" under the long text boxes, "Enter to send, ⌘/Ctrl + Enter for a new line" under the assistant's chat) are hidden, and everything that can be tapped dims a little while pressed.

## Search engines

Every public page has its title, description, canonical address and link-preview image, with the preview's address (the canonical), language (`og:locale`, and `og:locale:alternate` for its other languages) and the picture's `alt`. `e2e_tests/pages/public-heads.spec.ts` checks all of it on every public page, and that each language version names the same versions as English.

**Link-preview images:**

- The logo over the page's own title in its language, drawn by `app/preview/route.tsx` in the site's dark theme and Poppins (`frontend/assets/fonts`). Other scripts' letters come from Google Fonts. The picture is sent with `X-Robots-Tag: noindex`, so search engines don't list it while link-preview bots still fetch it. Each page's picture address carries a signature of its title and language (`PREVIEW_SECRET`), and any other title gets a 404, so nobody can put their own text under the logo.
- The home page uses the home page's promise instead (`app/opengraph-image.tsx`). So do Arabic, Persian, Hebrew and Hindi, which the renderer can't draw.

**Structured data:** organization (with its postal address in parts), product and price range (no rating until real reviews exist), founder, articles (with their picture and language), the developer docs as a technical article in English, breadcrumbs (role and practice pages, the API docs), FAQ (left out when there are no questions).

**Sitemap:** every language version, article, and the pages of each indexable template, dated by the template's last change; each language of an article by its own file's `updated`. Its calls to the API give up after 5 seconds. The news page is dated by its newest post, and the privacy policy, terms and DPA by their last update.

**Indexing:**

- Private pages (signed-in areas and personal links) answer with `X-Robots-Tag: noindex`.
- A template's role test and practice pages are indexable only when the template has at least 3 topics (`MIN_INDEXABLE_TOPICS`) and is the first template of its title in its language. Others say `noindex` and stay out of the sitemap.
- robots.txt blocks only `/api/` and `/monitoring`.
- `GOOGLE_SITE_VERIFICATION` and `BING_SITE_VERIFICATION` add Search Console's and Bing's ownership tags when set.
