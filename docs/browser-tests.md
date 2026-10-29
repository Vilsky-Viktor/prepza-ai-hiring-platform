# Browser tests

Playwright tests of the signed-out pages (`e2e_tests/pages`) and the signed-in pages
(`e2e_tests/signed-in`), each in Playwright's Docker image against the running stack. The other
suites are in [Testing](testing.md).

- [The browser tests' site](#the-browser-tests-site)
- [Browser tests of the signed-out pages](#browser-tests-of-the-signed-out-pages)
- [Browser tests of the signed-in pages](#browser-tests-of-the-signed-in-pages)

## The browser tests' site

Browser tests (`pages.sh`, `signed-in.sh`) never open the dev server you browse at
http://localhost:8090: it compiles each page on its first visit, grows past several GB under a
test run, and a run would slow it down for you. They open a production build of the frontend
instead, compose's `frontend-test` service (the `test` profile; `frontend/Dockerfile`'s `prod`
target with the local stack's `NEXT_PUBLIC_*` settings), behind the gateway's port 8082. That
port has the same API routes and services and the same Auth emulator as port 80; only its pages
come from the test build, and like port 8081 it isn't counted by the gateway's per-IP limit (every
parallel browser comes from one address). The browser still opens `http://localhost:8090`, mapped
to `gateway:8082`, so the site sees its usual address.

Each script hashes the frontend's files as they are (uncommitted changes too, but not
`frontend/tests`) with the build's settings (`e2e_tests/test_frontend.sh --source`) and, once it
has its browser slot, rebuilds and restarts the test site only when it was built from other files
(the hash is the container's `prepza.frontend-source` label). A rebuild takes about 2 minutes on a
laptop, as Next's build cache stays in a BuildKit cache mount between builds (6 to 10 minutes
with that cache empty, the first time); with the files
unchanged a run starts at once. Pages only the dev server has (`/report-samples`) aren't there.
The build is production's but for the local settings it's built with: with the sign-in emulator
set (never in production) its pages don't ask the browser to upgrade requests to https, which
Safari would do even on `http://localhost`.

Up to `BROWSER_RUNS` runs (default 2) use the stack at once, whoever starts them, and only runs of
the same frontend files: a run of other files waits for them to end, so the site is never rebuilt
under a run. A run of every signed-in spec, or of a spec with a `@global` test, has the stack to
itself. Runs take a slot in `e2e_tests/browser_lock.py` (a directory under
`.git/prepza-browser-runs`, shared by every worktree, holding the run's pid and frontend hash); a
later run prints "waiting for earlier browser runs" and starts in the order it came, and a slot
left by a killed run is taken over once its process is gone.

**Hidden copies of a page's parts.** A page streams in: React first parks a finished part in a
hidden `<div hidden id="S:0">` and moves it into place a moment later, and a part the browser
renders itself meanwhile is in the page twice until then. Role locators (`getByRole`) skip hidden
elements; `getByText`, `getByTestId` and CSS locators don't, so on a page that just loaded or
rendered again they take the visible one, `.filter({ visible: true })`, or an assertion can meet
two elements (a strict-mode error) or click the hidden one.

## Browser tests of the signed-out pages

Playwright tests of the signed-out pages in Playwright's Docker image, on a desktop and, where a phone's layout differs, a phone: every test runs in the `desktop` project, and only those tagged `@phone` (both sizes) or `@phone-only` also, or only, in the `phone` project (Pixel 7), so nothing is checked twice that looks the same on both. The pages (`pages.spec.ts`): home, companies, pricing (also in German and Japanese), terms, privacy, documents, FAQ, about, contact, practice, skills tests by role, and the articles (pre-employment testing, AI interviews, a comparison, a guide and their hubs). It also checks that the sign-in dialog offers its two email boxes, unticked.

They check:

- no console errors,
- no sideways scroll,
- the same page width everywhere,
- the footer at the end,
- lowercase titles (articles keep their capitals).

`landing.spec.ts` checks the home page: every section in order and within the window on a desktop and a phone, and in every language on a phone, the narrowest screen (the example's code too, which keeps its own size in Japanese, Chinese and Korean); with reduced motion every picture a still frame; the hero's box asking a visitor to sign in to start an interview; the hero's video button playing the video in a window; the pricing section's top-ups and free candidates from billing's catalog, with the receipt paying for the top-up with the lowest price per candidate; the comparison's price range from the catalog; the closing buttons to Mira, the demo videos, the FAQ and the guides. `landing-create.spec.ts` checks the create section's panels waiting for the earlier steps, its questions per topic, the finished interview with reduced motion, and each "create an interview" button going back up to the job description box, focused. Other specs check the catalog's free candidates on the pricing page and its rows lighting up on hover (`pricing.spec.ts`), smooth scrolling and back to top (`scroll.spec.ts`), the API docs (`api-docs.spec.ts`), the demo videos link opening YouTube and the footer's "ask Mira" (`demos.spec.ts`), and the info button opening its guide, which ends with a card across the dialog whose button opens the contact page (`page-help.spec.ts`). `assistant.spec.ts` checks the assistant signed out: FAQ answers only (stubbed: no OpenAI), a sign-in card when asked, a failed answer's Try again, a reload in the middle of a chat, Mira's name keeping its capital in the buttons and the welcome (in Russian; every language's messages in `frontend/tests/messages/landing-texts.test.ts`, as are the hero's two sentences, checked in the browser in English and Arabic), the phone header's icon-only button named like the footer's, and the panel and a dialog opening and closing fully with and without reduced motion. `phone-layout.spec.ts` checks the public pages on a phone: previews and the home page's box across the screen, the footer one centered column, dialogs across the screen, no keyboard hint on a touch screen, and a practice page starting under its tags. `phone-sub-pages.spec.ts` checks, on a phone, the bar naming the open one of a page's own pages (the MCP docs'): across the whole window, square and right under the tabs, opening the site's menu of every page in order with the open one marked, and a page chosen there opening at its address. `faq.spec.ts` checks that an FAQ answer's link opens its page in the same tab and stays in the address's language. `list-search.spec.ts` checks that a search and the list under it, or its empty state, read as one block on a computer and a phone: no gap, the same width, square corners where they meet and one border round both with a single line at the seam. `footer.spec.ts` checks the footer's three columns of links (the news page's among them), its menu and social icons named for screen readers and the icons not links, the company that runs prepza named in the footer and on the contact page (its email a link), and where the accessibility statement says to report a problem. `legal-versions.spec.ts` checks that every version of the terms stays readable, saying whether it applies, and shows in the page's language with a link to the binding English. `sign-in.spec.ts` checks that the sign-in card asks about emails only on a browser no one has signed in on. `contact.spec.ts` checks that the contact form shows no labels and each field keeps its accessible name, also once filled. `reading-pages.spec.ts` checks that an article links back to its section, and the about, accessibility and legal pages home, beside their title. `accessibility.spec.ts` runs axe (`@axe-core/playwright`, WCAG 2.2 A and AA rules) on the key public pages, light and dark, in English and in right-to-left languages, and with the sign-in dialog and Mira's panel open, with motion reduced so no animation is caught halfway; what it finds and can't be fixed at once is listed as a known issue in the spec, never by turning a rule off. `signed-in-links.spec.ts` checks that links into a company's pages (a scorecard, an interview, a template, a generation) opened signed out ask to sign in instead of answering "not found" (404). `link-errors.spec.ts` checks that an invite says its link is invalid only when it's gone, and offers to try again otherwise. `referral-notice.spec.ts` checks that a referral link is kept in a cookie only once the visitor agrees, and turning it down keeps nothing. `double-submit.spec.ts` checks that a contact message sent twice quickly goes once, and `error-report.spec.ts` that the error page's "Report" sends what the user was doing, and sits in the row of its other buttons on a computer and on its own line under them on a phone. `news.spec.ts` checks the news page in English and German whatever posts exist: indexable, its title, description, canonical and hreflang addresses (x-default too), link-preview picture, `Blog` structured data, the RSS link in its head and its RSS icon; the RSS feed in both languages (content type, channel, items linking to the page); and the sitemap listing the page but not the feed. `connect.spec.ts` checks the AI app consent page signed out: without a request it says the link expired, with one it asks to sign in first without reading the request, and it isn't indexed. `unsubscribe.spec.ts` checks the unsubscribe page: an invalid link says so, the page isn't indexed, and a candidate's link to a made-up company changes nothing until "Confirm". It signs that link with `EMAIL_LINK_SECRET`, which `pages.sh` passes from `.env` without printing it, and deletes its made-up company's opt-outs from the local notifications database when it ends.

Like every browser test, these check behaviour and data, never the wording: elements are found by role, position, structure or a `data-testid`, and only error messages and data (prices, dates, names the test passes) are matched as text. `seo.spec.ts` checks language addresses and hreflang, titles, preview pictures, articles and links; `seo-templates.spec.ts` checks the template pages: a role page, a template's languages and its page in its language (links and levels), old addresses' redirects, robots.txt and the sitemap, and which templates are indexable (noindex on thin ones). `metadata.spec.ts` checks page descriptions, noindex on private pages and personal links, FAQ data (an answer's links as their text) and article data, practice breadcrumbs, the direction of right-to-left template text and the preview picture's noindex. `public-heads.spec.ts` reads every public page's head as crawlers get it: its own title naming the site once, its own description, a canonical equal to its address, hreflang sets that agree between the language versions and a complete link preview. `currencies.spec.ts` checks the home page's and the pricing page's prices in a visitor's currency for two countries (euros, and złoty written with its code); billing's unit tests map every country to its currency and `format.test.ts` writes each one.

Tests that need a template never use the platform's own: each adds its own throwaway templates straight into the library database (`helpers/templates.ts`: a unique title and readable address, topics with subtopics and company and practice questions; at least 3 topics makes one indexable, fewer doesn't), checks only those, and deletes them when it ends. Before a run, a global setup (`global-setup.ts`) deletes the templates and opt-outs a stopped run left, once they're older than 6 hours, so runs at the same time keep each other's. `pages.sh` mounts `.env` read-only for `POSTGRES_PASSWORD`, read without printing it.

A test that wants light or dark calls `setScheme(page, scheme)` (`helpers/theme.ts`, one in each suite), which sets the device's setting and the visitor's saved choice, on the open page at once and on every page it loads next. `theme.spec.ts` checks that a new visitor follows their device, light and dark, and that a picked theme stays on a device set the other way (also after a reload).

```bash
./e2e_tests/pages.sh
```

Extra arguments go to Playwright, for example a spec's name. Tests run in parallel, within a file
too, `WORKERS` at once (default 3: the landing's moving pictures keep each browser busy, so more
only slow every page down); a test may take 60 seconds and an assertion waits up to 15, as in the
signed-in suite, since every worker's browser runs on one laptop's stack.

Review screenshots (`shot`, `helpers/screenshots.ts`) are taken only with `SHOTS=1` (`SHOTS=1 ./e2e_tests/pages.sh ...`): nothing compares them, and each costs a second or more.

Each run copies the specs into its container (a tar stream, as the signed-in suite does) and installs its own packages there, so runs at the same time don't share `node_modules` or see a file half-edited. Its traces and screenshots land in a folder of their own, `e2e_tests/pages/test-results/<run>` (the script prints it at the end): Playwright empties its results folder when a run starts, so a shared one would lose another run's traces. Folders older than a week are deleted at the next run.

## Browser tests of the signed-in pages

Playwright tests of the signed-in pages, in the same Docker image, against the running stack
(on [the browser tests' site](#the-browser-tests-site)).

**In parallel.** Every test owns its users and data, so tests run in parallel (`WORKERS`, default
3, as in the signed-out suite) and in any order. A test that changes what every page sees is tagged `@global`
(`{ tag: "@global" }`: the pause and maintenance mode, a limit, a news post
in every user's bell): those run in the `global` project after the others, one at a time with
nothing else running, and a run that includes them has the stack to itself. Each phase writes
its results to its own folder (`parallel/`, `global/`).

**Signing in.** Most tests sign in straight at the Firebase Auth emulator (local only): `signInAs` signs in with Google at its REST API with an unsigned Google ID token, which only the emulator takes, makes the calls the site makes at a first sign-in (the account's language, the sign-in's email choices) and opens a fresh browser context holding the session as the site's Firebase keeps it (its local storage) and its token cookie. The tests of signing in itself go through "Continue with Google" and the emulator's own sign-in page, ticking the sign-in's email boxes first where they test them (`signInAs(email, { ui: true, noUpdates, promotions })`): the owner's first sign-in, the email boxes, the sign-in filling a candidate's name, a join link opened by another account, the assistant's sign-in card, and each provider's popup. The superadmin is the first address in `SUPERADMIN_EMAILS`.

**Test data.** Every test makes throwaway users, companies and interviews. Interviews are made from local templates: no OpenAI. The owner spec adds and deletes its own throwaway templates in the library database.

**What they cover:**

- a company owner making an interview from a template and inviting a candidate,
- inviting candidates with names three ways (one email, a list, a file) and finding one by name, the sign-in filling in a name once with an owner's correction kept, and the invite dialog saying what it couldn't read,
- deleting an interview past the list's first page: it leaves the list at once, and the list goes on loading from the right place,
- a title under three characters and a one-letter company name, refused with the reason,
- a candidate taking an interview, a question's time running out included,
- a "select all that apply" question: ticked with check boxes, a partly right answer earning part of its point, and the scorecard, the practice review and the question lists showing it,
- a candidate leaving the page: only a leave of 2 seconds or more counts, and the results say signals are the browser's report,
- dates in the visitor's own time zone,
- a job ad's shareable link: starting from it, and continuing from the candidate's own link after it's turned off,
- an expired invite, which asks to have it sent again,
- a candidate whose email isn't confirmed, told to confirm it,
- signing in through each provider's popup (Google, LinkedIn, GitHub) under the site's `Cross-Origin-Opener-Policy`, which the pages send (`y-sign-in-providers.spec.ts`),
- the team and a viewer, and a join link opened while signed in with another email (a warning, no Join),
- a company's action log: the owner sees their own and another member's actions, with who did what, and filters them by member, kind of action and days; an admin and a viewer have no tab, and its page sends them to the company,
- handing a company to an admin, who's told in the bell, and deleting an account that owns a company others joined, which waits, then names the companies deleted with it and their credits,
- removing a company: the dialog says how many credits are lost, and nothing about credits when there are none,
- the companies page's cards (`zw-companies-cards`): three to a row on a laptop with their names level, one link per card named by the company that opens it from anywhere on the card, a logo covering its whole area, wide or tall, the first letter without one, and Remove opening its confirmation without leaving the page,
- verification,
- a stat icon (an interview's candidate count) reacting on hover like an icon button, its background and colour changing in light and dark, while staying out of the tab order (`zx-icon-stat-hover`),
- the admin zone's pass rates, stats, pause and maintenance mode (turned off again afterwards),
- the admin zone's support tab: finding a company by its ID, an interview by its link in another language, a candidate by their email in another case and a company by its name (and nothing for something unknown), an account first by its email and by its ID; a company's page: credit history, held credits, members, interviews and action log (who did what), adjusting its credits with a reason the company then sees in its own history, a removal below zero refused with its error, and suspending, lifting, renaming and deleting it (the old companies tab's address leading to support); an interview's page: a failed generation marked, its company, topics and candidates (a grade only for the finished one); a candidate's page: links to the company and interview, start and finish dates once finished, the grade and extra time; an account's page: its companies,
- the admin zone's news tab: the tabs' order, a post written in the dialog (the characters left, an over-long text refused by the API's message), shown in the tab and on the news page with its blue dot and date, shown in a user's bell, turned into a product update campaign from its row, edited with the pencil and deleted with the bin after confirming, leaving the bell. Its posts are deleted at the end, even when it fails,
- the admin zone's campaigns (`zm-campaigns.spec.ts`): a campaign written with the editor (bold and a link), its preview and recipients, a test sent to the superadmin's own address and read back from the local Mailpit (then deleted), its kind changed and the draft deleted; an account's support page showing its address on the suppression list and taking it off; the legal banner for a pending DPA change concerning one throwaway user, closed and still closed after a reload. Nothing is sent to users,
- the admin zone's important notices (`zm-campaign-notices.spec.ts`): a notice to one throwaway company's owners and admins, picked in the dialog's audience, its count matching the service's, its audience saved and shown, the send's button off until the box is ticked, and the service refusing a notice sent without it, with its message. Nothing is sent; the draft is deleted,
- the admin zone's support pages for people: an address found in another case giving its account first, then its candidates; on the account's page turning off all optional emails (still off after a reload) and marketing refused with its error; on a candidate's page stopping and resuming one inviting company's emails (still stopped after a reload) while the person's own stop has nothing to press; and the emails tab's old address leading to support; anyone else finds no admin page (`e-superadmin-access.spec.ts`), the support tab and their own account's and candidate's support pages included,
- the candidates' PDF report,
- a viewer emailing a report: an address outside the company refused with the reason, a member's address let through (`f-reports-viewer.spec.ts`),
- a practice result leading to a company's test,
- a talent's practice history, newest first, loading older rounds as it scrolls,
- a company's interviews searched by title in any case (`zz-interviews-search.spec.ts`): the search kept in the address after a reload and in the next page loaded as the list scrolls, and a search matching nothing showing the no-matches state,
- a practice round's time per question: the options the API sends, the picker beside the start, and an untimed round without a countdown (`zu-practice-timing.spec.ts`),
- text in another language than the page marked with its `lang` and `dir`: an interview's topics and questions, and each language's own name in the language picker (`zv-text-language.spec.ts`),
- an interview's settings tab, and the shareable link turned on at its top (not on the candidates tab) to give the link to copy,
- a candidate's invitation: their extra time doubling each question's time, and the pledge to answer on their own gating the start (`zt-start-pledge.spec.ts`),
- an interview's start page on a computer: the whole interview's minutes from its topics' questions and seconds, the big start button, and the rules card from the screen's top to its bottom, scrolling inside on a short screen (`zo-start-page.spec.ts`),
- a new hard test starting with the hard level's seconds a question, and the value saved in the admin zone's Controls and set back (`zn-level-seconds.spec.ts`; that it reaches the next new test is billing's integration test),
- a company's brand tab: colors previewed as they're typed, unreadable ones refused, the font and rounding saved with them, and its candidate's invitation in those colors,
- API keys and web hooks,
- a web hook's signed test event and its delivery log,
- the API's operations: inviting a candidate twice, with and without a client's Idempotency-Key (invited once; the retry is a `200`), a reused key with another body refused, correcting them, extra time, a reminder, finding them by email, the credits, removing them, and a new interview within the app's limits,
- a candidate invited through the API taking the interview without signing in and going back to the company's platform (any https return address, whatever the allowed domains; an http one off localhost refused),
- a company's own site embedding a candidate's interview and hearing it finish,
- each ATS: Workable's linked jobs, and connecting Greenhouse (with who connected it under its title), Teamtailor, Recruitee and Breezy HR,
- Slack,
- the MCP server: its row and Instructions (the server's address, Claude's and ChatGPT's steps, opening on the dialog itself with Close outside the scrolling body, full height on phones), the connected AI apps (saved straight into the assistant database and deleted at the end) and disconnecting them, and the consent page signed in (an expired request, and a request answered in the browser, denied),
- an AI app connected through the real authorization flow: it registers, the consent page names it, Allow gives it a code that becomes a token once (a second exchange is refused), and the AI apps page lists it,
- an owner stopping AI apps from using the company's data and allowing them again (kept after a reload), the switch right to left in Arabic,
- the company's bell saying when an ATS refuses the results written back, Slack stopped working or a web hook stopped, and opening that page to reconnect,
- the integrations pages on a phone: small logos beside the names with the buttons under them, the pages' buttons under their titles, Reconnect on its own line, the linked jobs, and full-height Instructions,
- "copy id" on a company, an interview, a candidate, Settings and the account menu, each copying its own ID,
- a company's billing: where the credits came from and went (a top-up, written as Paddle's web hook writes it, and a finished candidate's charge, opening their page) and the candidates whose credits are reserved, for owners and admins; a viewer has no billing tab, and its address sends them back to the interviews,
- a top-up opening the checkout the backend made in Paddle's overlay (skipped when Paddle's sandbox prices aren't in `.env`),
- a balance saying on hover that it's the current balance, in the company's header and on the billing page,
- the top-up slider mirrored right to left in Arabic, ArrowLeft adding,
- the automatic top-up,
- an interview whose generation failed,
- the assistant: the welcome for the user's stage (its title keeping Mira's name as written), an answer with a candidate row, voice through Chrome's fake microphone, the history, a reload in the middle of a chat, and a visitor who signs in from its sign-in card keeping their chat (answers stubbed: no OpenAI),
- the assistant's actions: one runs once its card is confirmed, asking to sign out signs out, and a pasted secret is removed from the chat and explained, with the page it belongs on,
- the assistant knowing the page (`p-assistant-page`, the real model, two messages; skipped without an OpenAI key, as in CI): on an interview's candidates tab, the message carries the page and its ids, "What can I do here?" reads the page's guide, and "Who's best here?" names that interview's candidate, not another interview's,
- the info buttons under the back arrow, one test a page, explaining the companies list, an interview's topics and candidates, a candidate, the team, the top-up and settings, each opening the guide site serves for its page, a candidate's guide linking its article; and the back arrow before the title with a gap on a wide screen, on the screen at 1280px, going home,
- the signed-in screens checked with axe (`y-accessibility.spec.ts`, WCAG 2.0 A and AA): a company's companies list, interviews, interview and its candidates, the invite dialog, a finished candidate's report, billing and settings in light and dark, and a candidate's invitation and question; known issues are listed in `helpers/accessibility.ts`,
- the signed-in pages on a phone: lists and panels out to the screen's edges, a long email on a candidate's page breaking before its @, actions on their own lines, dialogs across the screen with their buttons side by side, timed questions with nothing around them, and an invitation's rules before its start, out to the screen's edges, with the big start button,
- the page menus (`zs-side-menu`): a company's pages in order with the open one marked, the menu holding under the window's top while the page scrolls and scrolling on its own when taller than the window, and on a phone three tabs and the rest under "…", a page opened from there taking the third place,
- email settings: the defaults, each kind saved as it changes, the activity digest's box (all, none, some), and what the sign-in's email boxes turn on, at a first sign-in and a later one,
- unsubscribing: a user's activity digest link turns its four kinds off in Settings, and after a candidate's "Don't email me for <company>" link, the company's next invite to that address shows as undelivered. Links are signed with `EMAIL_LINK_SECRET` from `.env`.

**Cleanup.** Every throwaway address carries its run's tag (the run's container id, `RUN` in `helpers/users.ts`). After a run, `teardown.ts` deletes that run's throwaway accounts, and so their companies and data, and leftovers of stopped runs once they're over 6 hours old; another run's accounts are left alone while it may still be running, so runs at the same time don't delete each other's users (a deleted account is signed out at its next change). It fails if any of its own is left. It also runs before a run (a global setup), so a run starts without a stopped run's old leftovers.

Review screenshots (`shot`) are taken only with `SHOTS=1`, as in the signed-out suite. Each run's traces and screenshots land in a folder of their own, `e2e_tests/signed-in/test-results/<run>` (screenshots under its `screenshots/`; the script prints the folder at the end), so runs at the same time don't empty each other's; folders older than a week are deleted at the next run.

```bash
./e2e_tests/signed-in.sh            # or: ./e2e_tests/signed-in.sh specs/b-candidate.spec.ts
```
