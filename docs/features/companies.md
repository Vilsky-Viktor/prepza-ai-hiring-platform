# Companies

A company is where a hiring team works: its interviews, candidates, credits and team live under it. Companies' pages live under `/companies`; old `/company` links redirect.

A company's pages (interviews, templates, team, integrations, brand, billing, action log, referrals; brand and billing for owners and admins, the action log for the owner) are listed in a menu beside the page, under the company's name: on wide screens a column at the start side (the right in Arabic, Hebrew and Persian), each page with its icon, the open one on a grey row with its icon in the page's blue. The menu stays in view while the page scrolls, and scrolls on its own when it's taller than the window. On phones and narrow screens it's a row of tabs above the page: the first three, and the others under a "…" button (labelled "More pages"); a page opened from there takes the third place. A page with pages of its own (billing's history and reserved candidates, brand's general and theme pages) lists them under it in the menu while it's open, and on phones in a bar under the tabs naming the open one, which opens a menu of them. An interview's page, the API page, the admin zone and the developer docs have the same menu (`components/common/side-menu.tsx`).

- [Names](#names)
- [Team](#team)
- [Brand](#brand)
- [Verification](#verification)
- [Suspension](#suspension)
- [Action log](#action-log)
- [Page guides](#page-guides)
- [How it's built](#how-its-built)
- [Related pages](#related-pages)

## Names

- Company names are unique across prepza, ignoring case.
- A company can be renamed.
- A user's companies are listed by name, alphabetically, ignoring case, as cards on the companies page (`features/company/components/company-card.tsx`): three to a row on a laptop, two on a small tablet, one across the screen on a phone. Each card is square: the company's logo fills it above the name, covering the whole area (cropped evenly to fit), or its first letter in blue on a faint wash of the blue gradient without one, fading softly into the name row below it (the name on one line, the full name in its tooltip, and the count of interviews at its end); over the logo, the verified or pending badge with the owner's icon or the member's role, and Remove for the owner (it asks to confirm first), which shows while the card is hovered or holds keyboard focus, and always on touch screens. The whole card opens the company; hovered or focused, its border turns blue and the logo zooms in a little (not with reduced motion). Choosing a company for a template shows the same cards, without Remove.
- One person can own at most 3 companies (`MAX_OWNED_COMPANIES`, by default; see [Admin zone](admin-zone.md#limits)).

## Team

A company has one owner. On the company's **Team** tab, the owner adds a member's email with a role, **admin** or **viewer**, and the member is emailed the join link, in the owner's language and with the company's logo; the link also appears on the tab, to copy and pass on if the email doesn't arrive. The invite counts toward the owner's email limits. A refused invite says why (already invited, your own email, too many waiting, the email limits). A company holds at most 20 invites not yet accepted (`MAX_PENDING_INVITES`), and one that never topped up sends at most 10 a day (`MEMBER_INVITES_PER_UNPAID_DAY`), so invites can't be used to email strangers from prepza's domain. A visitor who isn't signed in sees the invitation (the company, not the invited email) with a **Sign in to join** button. When the member joins, the owner gets a [bell notification](notifications.md#what-gets-a-notification). A used link stays readable: the member who joined sees "You've joined" with **Open company**, anyone else "This invite has already been used"; joining again, even twice at the same moment, changes nothing and tells the owner once. An invite withdrawn meanwhile is not found (404), and the same email invited twice at once is refused the second time (409). Only someone signed in with that email can accept it, so a forwarded link is useless to anyone else. The owner can change a member's role later, and remove a member or withdraw a pending invite.

| Role | What they can do |
|---|---|
| Owner | Everything, including managing the team and removing the company |
| Admin | Works like the owner, except managing the team and removing the company |
| Viewer | Sees the company's interviews, questions, candidates and scorecards; downloads and shares reports (emails them only to the company's members); previews interviews. Changes nothing and spends no credits |

The companies service enforces the roles: `require_editor` answers 403 to a viewer.

### Handing the company on

The owner can make an admin who has joined the owner: the role picker on that admin's row has an **owner** choice (`can_own` in the team list says who), which asks to confirm first (`POST /companies/members/{id}/owner`). In one transaction the admin becomes the owner and the owner an admin, only while both are still what was read, so a company never has two owners or none. Someone who already owns 3 companies can't become an owner of another (409). The new owner gets a bell notification (`ownership_received`), and the [action log](#action-log) records it (`ownership_transferred`). An automatic top-up keeps charging the card of whoever set it up. It isn't one of the assistant's or AI apps' tools.

### Deleting an account that owns companies

The delete-account dialog asks companies what deleting the account does to the companies the user owns (`GET /companies/account/deletion`): one others have joined blocks it, listed with a link to its team, until another member is made its owner or the company is deleted; one only the user is in is deleted with the account, listed with its credits. Companies also refuses the deletion itself (409) while the user owns a company others joined; accounts asks companies first, so nothing is deleted then. Deleting the account also clears it as a company's verification proof (`verification_email`; the company keeps its verification) and takes the owner's "member joined" notification that names it; "Download my data" lists the companies it verified (`company_verifications`).

## Brand

A company's **brand** tab (owners and admins, like billing) sets how its candidates see the whole interview process: the invitation, the shared test link, the questions, the finished page, the embedded interview and a member's preview. Those pages never show prepza's header or footer, only the company.

Its settings are three pages of brand's, listed under it in the side menu: **general** (`/brand`: the logo, then the font and the rounding, each a group of its own), **light theme** (`?page=light`) and **dark theme** (`?page=dark`), each theme's colors. Each page has the preview beside its settings, "preview" on its top edge, and save and reset at the top and again under the settings; they save and reset what that page shows, and edits on another of brand's pages are kept while moving between them.

### Logo

A company can upload its logo: PNG, JPEG or WebP, up to 500 KB (a WebP is kept as PNG, with its transparency, since classic Outlook shows no WebP in emails; Pillow in companies, off the request loop, and only up to 4,096 pixels a side, read from the file's header first, so a small file declaring a huge image can't use up the service's memory), on the brand tab or by clicking the logo beside its name (hovering an editable logo shows an edit icon in its middle). It is shown on:

- invite and reminder emails, beside the title,
- the invite page and the interview candidates take, above the title on the finished screen,
- PDF reports.

### Font and corners

On the general page, under the logo: the font (by default prepza's pair, Poppins titles over Geist text; or one font for all the text, one of the most used web fonts: Inter, Roboto, Open Sans, Lato, Montserrat, Nunito, Raleway, Work Sans, Source Sans 3, Noto Sans, PT Sans, Ubuntu, Rubik, Manrope, DM Sans, IBM Plex Sans, Mulish, Fira Sans, Plus Jakarta Sans, Outfit, Merriweather, Lora and Playfair Display), and how round the corners are, 0–24 px: the cards' and the buttons', as drawn on the candidate's pages (14 px each by default, as on prepza's own site; the other corners scale with the cards'). Both are the same in the light and dark themes (`PUT /companies/{id}/brand-style`, `brand_font`, `brand_radius`, `brand_button_radius`). The site bundles each font (`config/brand-fonts.ts`, not preloaded): a page downloads only the one it uses, each falling back to Geist for letters it lacks.

### Colors

Two sets, one for the light theme and one for the dark, each in groups like a theme's: **page** (background, text), **primary** (buttons, the picked answer's outline, the timer, links; and the text on buttons), **secondary** (fills such as the rules box and the picked answer; the gray text), **dialogs** (background, text) and **borders**. Each starts from prepza's own (`PREPZA_COLORS`) and is saved on its own (`PUT /companies/{id}/brand-colors/{light|dark}`, merged in SQL into `brand_colors`, so two people saving the two themes keep both). Every text must read on its background at WCAG AA's 4.5:1 and the buttons on the page at 3:1, or saving is refused with the group to fix (`helpers/brand.py`), so no candidate is tested on a page they can't read. **Save** keeps what's on screen: the theme's colors, the font and the rounding. **Reset** brings back what was last saved; **reset to prepza defaults**, shown while anything saved isn't prepza's, goes back to prepza's colors in both themes, font and rounding (`GET /brand/prepza` gives them). A live preview (a sample HR question about branding, the start button and the finish dialog) shows the set being edited.

Which theme a candidate sees: the one the address asks for (`?theme=light`, `dark` or `default`, which the SDK passes), else the one the invite asked for through the API (`theme`), else the candidate's own light or dark setting. The candidate's pages set the theme variables of that set on the page (`hooks/use-brand-colors.ts`); without a set of its own, a theme is prepza's.

## Verification

A verified company has a check next to its name everywhere.

1. An owner or admin gives the company's website.
2. They prove its domain by signing in with a verified email on it. Free mail services don't count.
3. The company waits for a superadmin's review on the admin zone's **Verification** tab. Meanwhile a clock shows next to its name, for its members only.

The decision:

- **Approved:** a check shows next to its name everywhere.
- **Declined:** its owners and admins see why. It goes for review again only after its name or website changes.
- Both decisions reach the owners and admins in the bell.

Later changes:

- Renaming a verified, pending or declined company sends the new name for review, taking any check away.
- Changing the website starts over.

Until a company is verified, its invite pages and its invite and reminder emails say, in a small gray line, that prepza hasn't verified it. Verification only gives the badge: the API, the SDK, the return button and AI apps don't depend on it (embedding follows the company's [allowed domains](api.md#allowed-domains)).

## Suspension

A superadmin can suspend a company from the admin zone (see [Admin zone](admin-support.md)), and lift the suspension later. While it's suspended:

- its members still see it, with a notice saying so, but nothing in it can be changed,
- it invites nobody: new candidates are refused (an ATS keeps them waiting until the suspension is lifted),
- candidates who haven't started find its invites and shareable link invalid; those already in an interview can finish it.

## Action log

Every action a company's members take on it is logged: who took it, what it was and what it was about, when, and what it came through. The owner reads it on the company's **Action log** tab (after Billing; admins and viewers have neither the tab nor its page, which sends them to the company), newest first, loading more on scroll. Each row: the action and its target, then who (the member's email, or "A former member"), the date and time to the minute in the viewer's time zone, and through what. Filters, kept in the address: a member (one who joined), a group of actions, and a range of days (the page sends the chosen days' bounds in the viewer's time zone as instants; companies filters).

| Group | Actions |
|---|---|
| Interviews | created (from a description or a template), deleted, renamed, settings changed (time per question, a topic's question count, hired), shareable link on or off, a question regenerated, an answer key marked wrong, topics approved, passing grade changed |
| Candidates | invited, invite sent again, revoked, deleted, name changed, extra time given, results viewed, report emailed |
| Team | member invited, joined, removed, role changed, ownership handed on |
| Company | renamed, logo, brand colors or style, website sent for verification, AI apps allowed or stopped |
| Billing | a member's top-up paid, automatic top-up set up, changed or stopped |
| Integrations | an ATS connected, reconnected or disconnected, a job linked or unlinked; Slack connected, disconnected or its notifications changed; an API key created, deleted, its permissions changed (with what was taken away) or its allowed IPs changed; the allowed domains changed; a web hook added, tested or deleted |

**How it's recorded.** Companies records its own actions (`src/companies/repositories/audit.py`), the joining of a member in the same transaction as the join. Billing, ats, notifications and api save theirs in their outbox in the change's own transaction (`prepza_common.events.audit.add`, event `audit.recorded`), so an action is sent exactly when its change is saved, and retried until companies stores it (each service's outbox is flushed after the request and every minute). Companies stores an event once however often it comes (its id is unique in `audit_events.event_id`), at the time it happened rather than when it arrived, so a late event keeps its place; an event for a company deleted meanwhile is dropped. A member's views of one candidate's results are one row a day (UTC), moved to the latest view (a partial unique index and an upsert, so views at once make one row).

**What it keeps.** Each row has the group (the action filter's column), `target_kind` and `target_id`, and a `target_label` only for what isn't a person (an interview's title, an API key's name, a web hook's site, an ATS's or Slack channel's name), as it was then, so a deleted interview still reads. People are never copied in: candidates' and members' emails are looked up when the log is read (as the support page does), so a deleted candidate shows as such and the log never keeps a candidate's email.

**Through what (`via`).** Empty when a member acted in the app, `assistant` when the in-app assistant did it for them, `mcp` when an AI app connected over MCP did (with the key's id, `key_id`, when it was an agent signed in with an API key: [API keys](mcp.md#api-keys)), `api` when an API key did, as the member who made it, and `ats` when an ATS sent a candidate, invited as the member who connected it. Companies trusts that only from a service token the assistant signs (the `X-Assistant` header, checked like other service calls); a missing or invalid one counts as the app. A view through the assistant isn't counted as the "results viewed" step of the sign-up funnel.

**Reading it.** `GET /companies/{id}/actions?member_id&group&from&to&offset&limit` for the page; `GET /companies/{id}/audit` (the same actions, without who and what, also with an API key) stays for AI agents. Both are for the owner only: admins and viewers get 403, others 404. Actions are kept for 12 months, then the daily retention job deletes them, and they go with the company when it's removed. When a member deletes their account, their actions stay with the company without their id (`deleted-user`, set a batch at a time); their data export lists them.

## Page guides

Every page from the companies list inward has an info button (a question mark in a badge, labelled "About this page"): under the back arrow in the page margin, or right after the arrow on narrower screens. It opens a short guide to that page: what it's for, what you can do there and a tip or two. The companies list, each company tab (interviews, templates, team, action log, integrations, brand, billing, referrals), each interview tab (topics, candidates, settings), a new interview and its topic review and generation, the preview, a candidate's report, a template, choosing a company for a template, the ATS, Slack, API and AI apps pages, and the top-up page and Settings each have their own, in every language. The companies list's back arrow goes to the home page.

The guides live in the site service, beside the FAQ (`services/site/src/site_content/page_guides/<language>.json`, by the page's key from `prepza_common.ai.page_keys`), and `GET /api/site/help/pages/{key}` serves one in the page's language (English until it's translated; an unknown key is a 404). A page whose topic a guide article covers names it (`PAGE_ARTICLES` in site's `constants/help.py`: the interview's settings and a candidate's page name the guide on timing and extra time), and the dialog ends with a link to it, titled by the article in the page's language. Under the guide, every dialog ends with a card across its whole width asking the user to report a problem, suggest an idea for the page or ask for a missing feature, with a "contact us" button to the contact page. The info button's dialog and the assistant read the same route, so there's one text. Every page where the assistant's panel opens has a guide, also the ones without an info button (practice, pricing, news, the articles and guides, the FAQ, the documents and legal pages, and so on): each page registers its key (`usePageKey`, the info button, or `PageKey`), which the panel sends with each message (see [the assistant](assistant.md#the-page-the-user-is-on)). The admin zone has none.

## How it's built

Companies' routes and event handlers call services (`services/companies/src/companies/services/`), which open each transaction and pass it to the repositories; accounts, billing, generation, library, rounds and Redis are called outside it, so no call to another service waits inside a transaction. Every change an owner, admin or member makes is one save with its line in the [action log](#action-log): a rename, the AI apps switch, the logo, the brand colors and style, the website, a member's invite (with its email), role, removal or join (with the owner's notification), the hand-over of ownership (with the new owner's notification), a candidate's invite (with its email), removal, name or extra time, an emailed report, an interview's creation (generated or copied from a template), settings, title, topics' numbers of questions, shareable link and deletion. When billing, generation or library makes the change (an automatic top-up, the currency, an approved topic review, a regenerated question, an answer reported wrong), its line is saved after they answer. An account's deletion ends its memberships, erases its candidate invites and forgets its team invites and its verification proof in one save, after deleting the companies it owned alone; its lines in the log lose its id a batch at a time. A company's or an interview's invites, interviews and action log go a batch at a time, each batch its own transaction, so a deletion cut off midway goes on when run again; the company or interview itself goes last, with its event (each deleted interview with `interview.deleted`, naming its questions' set and generation). Rounds and library delete their copies from these events (candidates' sessions and answers; the questions), not by calls, so a deletion never waits on them or fails while they are down; deleting again deletes nothing more. A preview started while its interview is deleted loses its sessions at once (the event may reach rounds first), and a candidate's start does the same when the invite went meanwhile.

## Related pages

- [Interviews](interviews.md): making and running a company's interviews.
- [Candidates](candidates.md): invites, scorecards and reports.
- [Credits and payments](billing.md): the company's wallet and referrals.
- [ATS integrations](ats.md): connecting Workable, Greenhouse, Teamtailor, Recruitee or Breezy HR.
- [Notifications and emails](notifications.md#slack): a company's notifications in Slack.
- [Public API](api.md): API keys and web hooks for a company's own platform.
