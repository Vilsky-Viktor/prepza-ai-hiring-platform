# Languages

prepza works in 23 languages: the interface, error messages, generated interviews and emails.

## Supported languages

English, Russian, Ukrainian, Spanish, Portuguese, German, French, Italian, Polish, Dutch, Turkish, Arabic, Hebrew, Persian, Japanese, Chinese, Korean, Hindi, Indonesian, Thai, Vietnamese, Filipino and Estonian.

Arabic, Hebrew and Persian read right to left, on the site and in emails. On the site the layout uses logical classes only (`ms-`, `pe-`, `start-`, `text-start`; `tests/styles/logical-direction.test.ts` fails on `ml-`, `pl-`, `left-` and the like), arrows and progress controls mirror, and Base UI's sliders, menus and popups follow the page's direction (`DirectionProvider` in the root layout), arrow keys included. Text people type takes its own direction (`dir="auto"` on text fields). In an email every table states the direction, lists are indented on the right, and addresses and links inside the text keep reading left to right. The punctuation an email's layout adds between its pieces (the plain text's heading, a label before its link, a note after the footer) is each language's own (`services/notifications/src/notifications/templates/patterns.py`): full-width marks in Japanese and Chinese, a no-break space before a French colon, the danda in Hindi, no full stop in Thai.

## The interface language

- A public page's plain address is always in English (the address carries the language: `/de/pricing`), unless the visitor chose a language or came in through a language's address before.
- On a first visit, a private page (sign-in areas, invite and job ad links) opens in the browser's preferred language if it's supported, otherwise in English. Traditional Chinese (`zh-TW`, `zh-HK`, `zh-MO`, `zh-Hant`) is not served Simplified Chinese: the next preferred language, or English. The services read the API's `Accept-Language` the same way.
- A new account keeps the language it signed up in.
- The language can be changed in Settings.

## Language addresses

The public pages have an address in every other language: home, pricing, FAQ, about, contact, documents, practice, skills tests, and the articles with their hubs.

- A prefixed address carries the language: `/de/pricing`, or `/fr` for the home page.
- English keeps the plain address.
- The language versions are linked with hreflang, in the head and the sitemap alike. hreflang uses the codes search engines read: Filipino is `tl` and Simplified Chinese `zh-Hans`, while their addresses stay `/fil/` and `/zh/` (`HREFLANG_CODES` in `config/seo.ts`).
- `proxy.ts` serves a prefixed address from its page in that language.
- The footer's language menu, a slim grey pill right after the copyright (a languages icon, the page's language and a chevron), appears on a page with versions and lists them: each language a plain link to its version, the ones the page's hreflang names (`components/language-switch.tsx`). The names are in English and sorted (`lib/english-language-name.ts`) whatever the page's language, so a visitor who can't read the page still finds theirs.
- The plain address is always the English page, whatever language the visitor chose before, as its canonical and hreflang say (`proxy.ts` marks it, `i18n/request.ts` follows).
- A first visit through a prefixed address keeps that language as the visitor's choice, which pages with one address follow: signed-in pages, the legal pages and the developer docs.
- Links between such pages stay in the address's language; on a page with one address they lead to the chosen language's versions (`/de/pricing` from a German settings page; `components/localized-link.tsx`, `linkLocale` in `lib/site.ts`).

Some pages exist only in certain languages: a skills test page and a free practice page are in English and in their template's language only (see [Public site](site.md#skills-tests-by-role)).

## Fonts

Scripts other than Latin and Cyrillic use Noto fonts (`config/fonts.ts`), loaded only on pages that need them. The Japanese, Chinese and Korean fonts (`config/cjk-fonts.ts`) are only on pages in those languages, so other pages' stylesheets stay small. The heading font loads Latin Extended too, for Polish, Turkish and Estonian.

Per script (`styles/scripts.css`): Arabic and Persian get no letter spacing, which breaks their joined letters; headings in Arabic, Persian, Hindi, Thai and Vietnamese get taller lines for the marks above and below; Japanese, Chinese and Korean small text is a step larger. Initials and typed-out text count characters as people see them (`lib/graphemes.ts`), never splitting an emoji or a Hindi cluster.

## Language of interviews and emails

- An interview is generated in the language chosen in "generate in", next to the text box. It defaults to the interface language.
- The pasted text can be in any language; the interview follows "generate in".
- Invite emails follow the interview's language.
- Questions and options carry the interview's language and direction (`lang`, `dir`), wherever they show: the interview's topics and questions, a candidate's scorecard and report, the session a candidate plays, a practice round and a template's page. Screen readers read them in that language, and an Arabic interview reads right to left in an English interface.
- A language's own name ("日本語", "العربية") in a language picker carries that language.

## Checking translations

Every language must have every key of `en.json`, with the same placeholders and plurals:

```bash
docker compose exec frontend pnpm check:messages
```

The message tests (`frontend/tests/messages/numbers.test.ts`) also fail on a plural that lacks one of its language's forms (Russian's few and many, Arabic's six) and on a number in a message that isn't a plural or formatted (`{count, number}`). The articles' test (`frontend/tests/content/articles.test.ts`) checks their front matter, first heading and slug, and that every language has each article with the original's sections and links.
