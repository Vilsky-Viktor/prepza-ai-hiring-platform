# Public site

The pages anyone can open without signing in, and how search engines see them. Every public page also has an address in each language (see [Languages](languages.md#language-addresses)).

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

The first screen: "Test everyone. Hire the best.", what prepza does and its price per candidate, each sentence on a line of its own, an info button that explains in a dialog how prepza works and a play icon under it (named in its tooltip, with a blue ring pulsing out of it, left out with reduced motion) that plays prepza's video in a window on the page (YouTube's no-cookie player, loaded only when the window opens): in the margin on the title's start side on wide screens, side by side above the title on narrower ones; then the box to paste a job description. From tablets up, thin wires run from the window's edges into the box and out of it, with candidates moving along them. Under the box, a short line of facts: the number of languages, how long an interview takes to be ready, and no subscription. Submitting the box:

1. signs you in if needed,
2. asks which company the interview is for (or its name, for a first company),
3. starts the generation.

Below, the page follows a company's hiring, one section per screen, each with a short title, one sentence and a live picture that plays while it's on screen:

- **Create an interview in minutes:** three panels joined by arrows: a job description typed and sent; its topics adjusted by hand and by asking the AI, then approved; and their questions written, then the finished interview (its topics, a "Ready" badge and "Invite candidates") with a candidate invited to it. Under them a line of facts: that no subject expert is needed, how many questions are generated per topic (`INTERVIEW_QUESTIONS_PER_TOPIC` from the Controls tab, read from generation's public `GET /api/generate/sizes`; left out when generation doesn't answer), and that ready-made templates are available. From laptops up the panels sit in one row; below, one under another, and reaching the last panel skips its picture ahead to the questions being written, so it never waits empty while the first two play off screen. On phones the facts are one a row, each after a blue dot.
- **Invite candidates from everywhere:** the interview in the middle, wired to every way candidates come in: your ATS, email invites, bulk imports, a share link in a job ad, the API, the embedded SDK, an AI agent and AI apps over MCP, with candidates counted in as they arrive.
- **What candidates see:** the invitation in the company's brand with the interview's rules, then a single-choice, a multi-choice ("Select all that apply") and a practical question answered.
- **See who's best, share it in seconds:** an interview's candidates and report emailed, then a candidate's report shared to a chat as a text summary; then "Create an interview", which goes back up to the job description box, ready to type, and beside it "Report samples", which downloads `prepza-report-samples.zip`: the report of all candidates and one candidate's report as real PDFs, from made-up data ([Reports](candidates.md#reports)). On phones the two buttons stack.
- **Automate your hiring:** your platform (API, SDK embed, web hooks), an AI app (MCP server) and a job board (share link) wired to prepza, and Slack getting the updates; under the section's text, a link to the developer docs (`/api-docs`).
- **Just ask the agent:** the assistant's panel answering how many candidates passed, how to give extra time (from a guide) and inviting a candidate once confirmed, beside what it does: info, help and actions.
- **Trust, quality and compliance:** the loop that keeps questions good (generated, checked blind by a second AI, answered and rated by candidates, flagged, rewritten), then four cards: a person decides, fair to every candidate, built for compliance (with a link to the documents) and every action on record.
- **Better than phone screens, cheaper than subscriptions:** phone screens, testing tools and prepza side by side, by how the questions are made, your time and what you pay, with prepza's price range per candidate and a link to the comparisons with other tools.
- **Everything is free, pay per candidate:** a receipt for a whole interview where every step costs nothing and only the candidates who answered are paid for, at the top-up with the lowest price per candidate; beside it the free candidates to start, every top-up with its price per candidate (the receipt's marked), "Create an interview" and "See pricing", and the small print (no subscription, unanswered invites cost nothing, credits never expire, unused paid credits refundable for 14 days).
- **The closing screen:** "Create your first interview. It's free." with "Create an interview" and the free candidates, then "More questions?" with buttons to ask the agent, the demo videos on YouTube, the FAQ and the guides.

Prices, the price range and the free candidates come from billing's catalog, so they follow any change; without the catalog the page shows without the comparison and the pricing sections. Nothing in the pictures is real data. Signed-in users see the landing page too. On phones every picture fits the screen and the pictures' soft bands reach its edges. A picture plays once 40% of it is on screen, or, for one taller than that (stacked panels on phones), once it fills 40% of the screen; scrolling within it doesn't start it again. With reduced motion every picture shows a still, complete frame (in the create section, the finished interview).

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
- Each has a short frontmatter: `title`, `seoTitle`, `description`, `updated`.
- `lib/content.ts` and `components/content/` show them.
- A new file is a new page, in its hub and the sitemap.
- The guides (`guides/` and each language's) are also what the assistant reads for hiring advice: rounds serves them from the same files (`GET /api/rounds/help/guides`, the list by title, and `GET /api/rounds/help/guides/{slug}`, one with its Markdown, in the page's language, English until translated). Its image copies `frontend/content` to the same place relative to its code as in the repo, the local stack mounts it, and CI rebuilds rounds when a guide changes, so there's one copy of each article.

**Translations** live in `content/<language>/<folder>/`, under the same file name.

- A page shows its translation in the interface's language.
- Where there is none, it shows English, with a note.
- It names only its real translations, for hreflang and in the sitemap.

**Comparisons** name no competitor prices and say where each tool fits better; prepza is presented as complementary.

## FAQ and help chat

`/faq` has the common questions, in the interface language, with today's prices; its intro points to the assistant ("ask agent" in the header) for anything else. Without prices (billing not answering), rounds refuses the FAQ (503) instead of building it with blanks: the site keeps showing the last good page, a role page leaves its FAQ section out, and the help chat answers without prices.

The questions are in `services/rounds/app/constants/faq/<language>.py`; a question not translated yet shows in English. An answer is plain text that may link to the site's own pages as `[text](/path)` (a guide, pricing, the API docs, ...): the page shows it as a link that opens in the same tab, in the address's language (`components/faq-list.tsx`, `FAQ_MARKDOWN` in `lib/markdown.ts`). Only a path on the site becomes a link; any other target stays its text, and the rest of the answer is shown as text. Every language links the same pages as English, in the same order (`tests/unit/test_faq.py`). The FAQ's structured data has each answer as plain text, its links as their text; the help chat and the assistant read the answers with their links as written.

The help chat (rounds' `POST /help/chat`) answers signed-out visitors in the [assistant's panel](assistant.md#the-panel):

- It answers only from the platform guide, the FAQ, the prices, the terms and the privacy policy, and keeps to prepza and hiring with it, like the assistant (`prepza_common.scope.SCOPE_RULE`).
- It answers in the page's language.
- Each question carries the key of the page it's asked on: the chat reads that page's guide, so "this page" and "here" mean it (see [page guides](companies.md#page-guides)). Every page with the panel has a guide, the public ones (pricing, practice, news, the articles, the FAQ, the documents) too; rounds serves them at `GET /api/rounds/help/pages/{key}`, which the info buttons read.
- A visitor shows they're a person ([the "I'm not a robot" check](../architecture.md#the-im-not-a-robot-check)) until their conversation has a reply.
- An answer's tokens count against the day's budget however it ends: estimated (about 4 characters each) when the model was cut short and reported none.
- Nothing of the conversation is stored: the panel sends it whole each time. Each reply ends with its signature (`{"done": true, "signature"}`, an HMAC of its text with the service's secret), which the panel sends back with it; the model reads every question but only the replies the chat signed, so a reply the page made up can't steer it, and only a signed reply spares the check.
- Each reply's last event also names the answer for a vote on it: `"answer": {"id", "trace_id", "signature"}` (a new id, its Langfuse trace when Langfuse is set up, and an HMAC of both). A thumbs up or down under it goes to `PUT /help/answers/{id}/vote` (`{"trace_id", "signature", "value": 1 | -1 | null}`, public): a wrong signature is refused ("There's no such answer."), so only the page that got the answer votes on it. Rounds keeps only the vote, by the answer's id, with its trace (`help_votes`; no text, question or voter), deletes it when cleared, and sends it on to Langfuse like the assistant's ([Votes in Langfuse](assistant.md#votes-in-langfuse)).
- A conversation with a secret in it (a key, a token, a password) is answered at once with a fixed reply, before the limits or the model, and nothing of it is used; see [the assistant's secrets](assistant.md#secrets-pasted-into-the-chat).
- A visitor asking to sign in or sign up, or to do something that needs an account (create a company, …), gets a sign-in card in the panel (the site's own sign-in buttons, the way they named first): the model starts its reply with a `[[sign_in:<provider>]]` marker, which the service turns into a `{"block": {"kind": "sign_in", "provider"}}` event.
- The same knowledge, with the FAQ in the page's language, is served as text at `GET /api/rounds/help/guide` (public, kept for 5 minutes per language); the in-app assistant reads it to answer questions about prepza.

Every limit but an answer's length and Cloud Armor's is one of `prepza_common.limit_list`'s: it starts at its default, and a superadmin changes it in the admin zone's Controls tab (see [Admin zone](admin-zone.md#limits)).

| Limit | Where it's set | Default |
|---|---|---|
| Messages an hour per account | `HELP_USER_LIMIT` | 30 |
| Questions an hour per address | `HELP_IP_LIMIT` | 60 |
| Questions a day in all | `HELP_DAILY_LIMIT` | 5,000 |
| An answer's length, in tokens | `HELP_MAX_OUTPUT_TOKENS` constant | 1,500 |
| Tokens a day in all (input and output, counted after each answer; a started answer finishes) | `HELP_TOKENS_PER_DAY` | 50,000,000 |
| AI spend a day of unpaid companies and people without a company, the help chat's visitors included (503 until midnight UTC once reached) | `AI_SPEND_UNPAID_DAY` | $15 |
| Questions per 10 minutes per IP, at the edge (Google Cloud only) | Cloud Armor (Terraform) | 20 |

Each answer is recorded with its tokens and cost as a `help_chat` AI call (see [Credits and payments](billing.md#ai-usage-and-limit-hits)).

The chat's model is set in [Generation settings](../generation.md#models).

## Legal pages

- The privacy policy, terms and data processing agreement are served by the rounds service (`GET /help/legal/{terms|privacy|dpa}?version=&language=`). The help chat answers from the English texts.
- **Languages:** each version is written in English, the binding text (each document's intro says so), and translated into the other 22 languages. A page shows its language's translation, saying it's a translation with a link to the English (`?language=en`); Arabic, Hebrew and Persian read right to left. Translations sit next to the English copy, at `app/legal_versions/<document>/<version>/<language>.json` in rounds, and a test requires every language for each current version, with the English's sections, paragraphs and items, and its addresses, links, numbers and dates. An older version without translations shows in English, saying so.
- **Versions:** each document's version is the day it applies from (`LEGAL_VERSIONS` in `prepza_common.constants`), and may come after the day it's published. Each page says "In force since …", or "Applies from …" with a link to the version in force now. Every published version stays readable (`/terms?version=2026-10-10`, which says it was replaced), listed under **All versions**. Rounds keeps a copy of each in `app/legal_versions/<document>/<version>.json`, the current one too, and a test fails when a text changes without a new version: give it one, then run `python -m app.legal_archive` in rounds. Rounds decides which version applies today and whether the one shown is in force, upcoming or replaced.
- **Acceptance:** signing up accepts the terms in force (the sign-in says so, and that the privacy policy was read), and library keeps that version and when (`terms_acceptances`; in the data export, deleted with the account). A company keeps the DPA version in force when it was made (`companies.dpa_version`), which its owner accepted with the terms. A later version applies after its notice; the terms say that using prepza after that day accepts it.
- **Notices:** a significant change is emailed at least 14 days before it applies, from the admin zone (see [Legal notices](admin-zone.md#legal-notices)). It goes in the bell too, and until it applies a thin banner above every page tells signed-in users from when, with a link to it; closing it keeps it closed in that browser for that version (see [Notifications](notifications.md#legal-notices)).
- The contact address in them, hello@prepza.ai, is put together in the browser, so the page's HTML doesn't hold it for bots to collect.

## Documents for companies

The `/documents` page ("legal docs" in the footer) offers companies:

- instructions for use, as a PDF,
- the data processing agreement, as a PDF,
- candidate notice and DPIA templates, as editable Word files.

Their sources are the Markdown files in `frontend/content/documents`, in English only, like the legal pages. The DPA's text must match `services/rounds/app/constants/dpa.py`.

After changing one, rebuild the files in `frontend/public/documents` and commit them:

```bash
./scripts/documents/build.sh   # needs uv (for pandoc) and Docker (Chromium prints the PDFs)
```

## Developer docs

The `/api-docs` page ("developer docs" in the footer) is the public API's reference, in English only, like the legal pages. It reads the API's OpenAPI description on each request (`lib/openapi.ts`, `components/api-docs/`) and shows it in five tabs (`?tab=`, `constants/api-docs.ts`), the description split at its `# ` titles, except MCP's:

- **API** (the page's own address): getting a key, authentication, limits, errors, sending candidates from your own platform and verified companies, then the base URL and each route with its parameters, body, result and errors;
- **web hooks**: signatures and delivery, then the `candidate.finished` event;
- **SDK**: embedding the interview with the hosted script, with a code example;
- **MCP**: connecting AI apps and one's own agents to prepza's MCP server, with example agents in Python and TypeScript and the server's tools (its own English text in `constants/mcp-docs.ts` and `content/mcp/`; see [AI apps over MCP](mcp.md#connecting));
- **objects**: what the routes and the web hook return; a type anywhere links to its object here.

The description's text may hold bold, inline code, links (`[text](/api-docs?tab=sdk)`: the API tab links its mentions of the web hook and of embedding to their tabs) and code blocks, each with its language ("```python"); code blocks that follow each other are one example in several languages, such as the routes' examples in curl, Python and JavaScript (`app/constants/docs.py` in the api service). See [Public API](api.md).

### Code

Code anywhere on the site shows in one editor (`components/code-editor.tsx`): a header with its language and a copy button, then numbered lines in the language's colors (shiki's GitHub themes, light and dark, loaded on first use; plain until then or for a language shiki doesn't know). An example in several languages gets a language menu in the header instead, and picking one switches every editor on the page that has it (kept while the tab stays open, `lib/code-language.ts`). The developer docs, the articles and the assistant's answers (Markdown code blocks, `components/markdown-code.tsx`) use it, and so does a question's example in interviews and practice, without the header (`lib/question-text.ts` reads the block's language from its fence).

## Contact us

`/contact` is a form with a name, an email and a message.

- The message is emailed to hello@prepza.ai (`CONTACT_EMAIL` in notifications).
- The visitor's address is the reply-to, so answering the email answers them.
- The sender shows they're a person first ([the "I'm not a robot" check](../architecture.md#the-im-not-a-robot-check)).
- At most 5 messages a day per address (`CONTACT_IP_LIMIT`) and 200 a day in all (`CONTACT_DAILY_LIMIT`) by default; both are edited in the admin zone's Controls tab.

### IDs to quote

So support finds what a message is about at once, the page asks visitors to paste the ID of what they write about. Each one has a "copy id" button (`components/entity-id.tsx`) that copies its ID and shows a check mark for 3 seconds:

- a company's, under its name in the company's header;
- an interview's, under its title, beside its status (also while it generates, or after it failed);
- a candidate's invite, on the line under their email;
- the account's (the Firebase uid), as a small button under the email in the account menu, and as a button in Settings, under "Your account".

The FAQ ("How do I report a problem?") and the help chat and assistant's guide say the same. An email shown large (a candidate's page, the candidate, team and credits-held lists, the interview report) breaks before its `@` when it doesn't fit (`components/wrapped-email.tsx`), so it never runs off a phone's screen.

## News

`/news` ("prepza news.") lists prepza's posts newest first, one after another: title (ending with the blue dot, like the site's headings), date and text. No pictures, links or detail pages; the text is plain, with its line breaks. Superadmins write them in the [admin zone](admin-zone.md#news).

- Posts are written in English and translated into every other language after they're saved. Each language's page (`/de/news`, …) shows its translation, or the English post while there's none.
- The first page is rendered on the server; the next loads when you scroll near the end (library's public `GET /news?offset=&limit=`, in the `Accept-Language` language, no sign-in).
- Posts are read fresh on every request, not through the public data cache, so a new, changed or deleted post shows at once (`lib/news-posts.ts`).
- **In the bell:** each post reaches every signed-in user's bell, named in their language, opening it here; deleting the post takes it back (see [Notifications](notifications.md#the-bell)). News isn't emailed by itself: a superadmin can send a post as a product update to those who chose them.
- **Search engines:** its own title and meta description in each language, canonical and hreflang addresses for every language, the link-preview picture, and structured data: a `Blog` with the page's posts as `BlogPosting`s by prepza (`newsData` in `lib/structured-data.ts`). The sitemap lists it in every language, dated by its newest post.
- **RSS:** `/news/rss.xml` (and `/de/news/rss.xml`, … in each language, with the same translations) is an RSS 2.0 feed of the newest 50 posts: each with its title, its text as plain text, its day and its id as the guid, linking to its place on that language's news page (`#<id>`). The page names it in its head and links it with the large RSS icon on the right of its title. It isn't in the sitemap.

## About us and the footer

`/about` explains why prepza exists for companies, free practice for people preparing, and its solo founder.

`/accessibility` is the accessibility statement (the EU Accessibility Act; candidates are consumers): the WCAG 2.2 AA aim, what prepza does (themes, brand colors held to WCAG contrast, 23 languages with right-to-left, phone layouts, text-only questions, extra time a company gives, and the keyboard: a "Skip to content" link first on every page, tabs moved with the arrow keys, form errors announced), what falls short (timed questions, no independent audit yet, Paddle's and Cloudflare's parts), where to write (answered within 14 days) and the Estonian authority (TTJA), with the day it was last reviewed (`constants/accessibility.ts`). It's in every language.

The footer names the company that runs prepza ("© <year> Arcolabs OÜ"); the contact page gives its registry code, address and email, every email ends with its name and address, and the home page's structured data has them too (all from `OPERATOR` in `prepza_common.constants`, mirrored in `frontend/constants/operator.ts`). The footer has the social icons and "ask agent", which opens the assistant, and its links in three columns: the product (skills tests, pre-employment testing, AI interviews, free practice, comparisons), resources (guides, FAQ, docs, API docs, news) and the company (About us, Contact us, privacy, terms, accessibility). On phones everything is centered, with the links in one column. Pricing is in the header's menu, not in the footer.

On phones dialogs and menus span the screen's width, with square corners. A dialog's buttons stay in sight at its bottom edge, with only its body scrolling, and help dialogs fill the screen. Lists, search boxes and gray panels reach the screen's edges, a page's main button ("new company", "new interview", "add member") takes its own full-width line under the title, and rows put their numbers and buttons under their title. On touch screens the keyboard hints ("⌘/Ctrl + Enter to send" under the long text boxes, "Enter to send, ⌘/Ctrl + Enter for a new line" under the assistant's chat) are hidden, and everything that can be tapped dims a little while pressed.

## Search engines

Every public page has its title, description, canonical address and link-preview image.

**Link-preview images:**

- The logo over the page's own title in its language, drawn by `app/preview/route.tsx` in the site's dark theme and Poppins (`frontend/assets/fonts`). Other scripts' letters come from Google Fonts. The picture is sent with `X-Robots-Tag: noindex`, so search engines don't list it while link-preview bots still fetch it. Each page's picture address carries a signature of its title and language (`PREVIEW_SECRET`), and any other title gets a 404, so nobody can put their own text under the logo.
- The home page uses the home page's promise instead (`app/opengraph-image.tsx`). So do Arabic, Persian, Hebrew and Hindi, which the renderer can't draw.

**Structured data:** organization, product and price range, founder, articles (with their picture and language), the developer docs as a technical article in English, breadcrumbs (role and practice pages, the API docs), FAQ (left out when there are no questions).

**Sitemap:** every language version, article, and the pages of each indexable template, dated by the template's last change. The news page is dated by its newest post, and the privacy policy, terms and DPA by their last update.

**Indexing:**

- Private pages (signed-in areas and personal links) answer with `X-Robots-Tag: noindex`.
- A template's role test and practice pages are indexable only when the template has at least 3 topics (`MIN_INDEXABLE_TOPICS`) and is the first template of its title in its language. Others say `noindex` and stay out of the sitemap.
- robots.txt blocks only `/api/` and `/monitoring`.
- `GOOGLE_SITE_VERIFICATION` and `BING_SITE_VERIFICATION` add Search Console's and Bing's ownership tags when set.
