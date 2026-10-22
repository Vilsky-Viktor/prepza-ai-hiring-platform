# Languages

prepza works in 23 languages: the interface, error messages, generated interviews and emails.

## Supported languages

English, Russian, Ukrainian, Spanish, Portuguese, German, French, Italian, Polish, Dutch, Turkish, Arabic, Hebrew, Persian, Japanese, Chinese, Korean, Hindi, Indonesian, Thai, Vietnamese, Filipino and Estonian.

Arabic, Hebrew and Persian read right to left, on the site and in emails. In an email every table states the direction, lists are indented on the right, and addresses and links inside the text keep reading left to right.

## The interface language

- A public page's plain address is always in English (the address carries the language: `/de/pricing`), unless the visitor chose a language or came in through a language's address before.
- On a first visit, a private page (sign-in areas, invite and job ad links) opens in the browser's preferred language if it's supported, otherwise in English.
- A new account keeps the language it signed up in.
- The language can be changed in Settings.

## Language addresses

The public pages have an address in every other language: home, pricing, FAQ, about, contact, documents, practice, skills tests, and the articles with their hubs.

- A prefixed address carries the language: `/de/pricing`, or `/fr` for the home page.
- English keeps the plain address.
- The language versions are linked with hreflang.
- `proxy.ts` serves a prefixed address from its page in that language.
- A first visit through a prefixed address keeps that language on the next pages.
- Links between such pages stay in the address's language (`components/localized-link.tsx`, `lib/locale-path.ts`).

Some pages exist only in certain languages: a skills test page and a free practice page are in English and in their template's language only (see [Public site](site.md#skills-tests-by-role)).

## Fonts

Scripts other than Latin and Cyrillic use Noto fonts (`constants/fonts.ts`), loaded only on pages that need them. The Japanese, Chinese and Korean fonts (`constants/cjk-fonts.ts`) are only on pages in those languages, so other pages' stylesheets stay small.

## Language of interviews and emails

- An interview is generated in the language chosen in "generate in", next to the text box. It defaults to the interface language.
- The pasted text can be in any language; the interview follows "generate in".
- Invite emails follow the interview's language.
- Questions and options carry the interview's language (`lang`), so screen readers read them in it whatever the interface language.

## Checking translations

Every language must have every key of `en.json`, with the same placeholders and plurals:

```bash
docker compose exec frontend pnpm check:messages
```
