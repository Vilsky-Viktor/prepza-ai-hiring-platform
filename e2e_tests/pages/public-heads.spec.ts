import { expect, test, type APIRequestContext } from "@playwright/test";

import { REQUEST_URL } from "./helpers/env";

// What every public page tells search engines and link previews, read from the HTML as crawlers
// get it: its title and description, a canonical equal to its own address, hreflang sets that
// agree between the language versions, and a complete link preview. Wording is never checked.

// Pages with an address in every language (constants/seo.ts LOCALIZED_PATHS), and one article of
// each kind.
const LOCALIZED = [
  "/",
  "/pricing",
  "/faq",
  "/about",
  "/contact",
  "/accessibility",
  "/documents",
  "/practice",
  "/tests",
  "/compare",
  "/guides",
  "/pre-employment-testing",
  "/ai-interviews",
  "/news",
  "/compare/testgorilla",
  "/guides/hiring-engineers",
];
// Pages with one address.
const SINGLE = ["/privacy", "/terms", "/dpa", "/api-docs"];
// hreflang codes: two letters, a script where one is named, and the default.
const HREFLANG = /^([a-z]{2}(-[A-Z][a-z]{3})?|x-default)$/;

type Head = {
  title: string;
  canonical?: string;
  alternates: Record<string, string>;
  meta: Record<string, string[]>;
};

function attributes(tag: string) {
  return Object.fromEntries(
    [...tag.matchAll(/([\w:-]+)="([^"]*)"/g)].map(([, name, value]) => [
      name.toLowerCase(),
      value.replaceAll("&amp;", "&"),
    ]),
  );
}

/** The page's head as served: its title, canonical, hreflang links and meta tags. */
async function readHead(request: APIRequestContext, path: string): Promise<Head> {
  const response = await request.get(`${REQUEST_URL}${path}`);
  expect(response.status(), path).toBe(200);
  expect(response.headers()["x-robots-tag"], path).toBeUndefined();
  const html = await response.text();
  const head = html.slice(0, html.indexOf("</head>"));
  const parsed: Head = {
    title: head.match(/<title>([^<]*)<\/title>/)?.[1] ?? "",
    alternates: {},
    meta: {},
  };

  for (const [tag] of head.matchAll(/<(link|meta)\s[^>]*>/g)) {
    const found = attributes(tag);

    if (found.rel === "canonical") {
      parsed.canonical = found.href;
    } else if (found.rel === "alternate" && found.hreflang) {
      parsed.alternates[found.hreflang] = found.href;
    } else if ((found.property ?? found.name) && found.content !== undefined) {
      const key = found.property ?? found.name;
      parsed.meta[key] = [...(parsed.meta[key] ?? []), found.content];
    }
  }

  return parsed;
}

/** The checks every public page passes; `address` is its absolute address. */
function checkHead(head: Head, address: string) {
  const one = (key: string) => head.meta[key]?.[0];

  expect(head.title, address).toMatch(/^.+ · prepza\.$/);
  expect(one("description"), address).toBeTruthy();
  expect(head.canonical, address).toBe(address);
  expect(one("og:url"), address).toBe(address);
  expect(one("og:title"), address).toBeTruthy();
  expect(one("og:description"), address).toBe(one("description"));
  expect(one("og:locale"), address).toMatch(/^[a-z]{2}(_[A-Z][a-z]{3})?$/);
  expect(one("og:image"), address).toMatch(/^https?:\/\//);
  expect(one("og:image:width"), address).toBe("1200");
  expect(one("og:image:height"), address).toBe("630");
  expect(one("og:image:alt"), address).toBeTruthy();
  expect(one("twitter:card"), address).toBe("summary_large_image");
}

test("every public page in English has its own head", async ({ request }) => {
  test.setTimeout(600_000);
  const descriptions = new Set<string>();
  const titles = new Set<string>();

  for (const path of [...LOCALIZED, ...SINGLE]) {
    const head = await readHead(request, path);

    // The site's own address (SITE_URL), which the request's isn't inside the test container.
    checkHead(head, new URL(path, head.canonical).href);
    descriptions.add(head.meta.description[0]);
    titles.add(head.title);

    if (SINGLE.includes(path)) {
      expect(Object.keys(head.alternates), path).toHaveLength(0);
      continue;
    }

    // Itself, the others and the default, by codes search engines read.
    expect(head.alternates.en, path).toBe(head.canonical);
    expect(head.alternates["x-default"], path).toBe(head.canonical);
    expect(Object.keys(head.alternates).every((code) => HREFLANG.test(code)), path).toBe(true);
    expect(head.meta["og:locale:alternate"]?.length, path).toBe(
      Object.keys(head.alternates).length - 2,
    );
  }

  // Each page's title and description are its own.
  expect(titles.size).toBe(LOCALIZED.length + SINGLE.length);
  expect(descriptions.size).toBe(LOCALIZED.length + SINGLE.length);
});

test("every language version names the same versions as English", async ({ request }) => {
  test.setTimeout(600_000);

  for (const path of LOCALIZED) {
    const english = await readHead(request, path);

    // German, and Filipino and Chinese, whose hreflang codes differ from their prefixes.
    for (const [code, prefix] of [
      ["de", "de"],
      ["tl", "fil"],
      ["zh-Hans", "zh"],
    ]) {
      const address = english.alternates[code];
      expect(new URL(address).pathname, path).toBe(
        path === "/" ? `/${prefix}` : `/${prefix}${path}`,
      );
      const version = await readHead(request, new URL(address).pathname);

      checkHead(version, address);
      expect(version.alternates, address).toEqual(english.alternates);
      expect(version.meta["og:locale"]?.[0], address).toBe(code.replace("-", "_"));
    }
  }
});
