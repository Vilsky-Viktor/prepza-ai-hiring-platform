import { afterEach, beforeEach, describe, expect, it, vi } from "vitest"

import { ApiError } from "@/lib/api"
import {
  answerHref,
  answerParts,
  helpConversation,
  withCard,
  withoutSignIn,
  withoutSecret,
  inAppHref,
  linkPage,
  pageCompany,
  transcribe,
} from "@/lib/assistant"
import type { AssistantBlock } from "@/types/assistant"

// No Firebase in a unit test: nobody is signed in.
vi.mock("@/lib/firebase", () => ({
  firebaseAuth: async () => ({
    authStateReady: async () => {},
    currentUser: null,
  }),
}))

const COMPANY = "8c1d2b8e-1a2b-4c3d-8e9f-0a1b2c3d4e5f"

describe("inAppHref", () => {
  it("keeps the app's own paths", () => {
    expect(inAppHref("/companies")).toBe("/companies")
    expect(inAppHref("/faq#credits")).toBe("/faq#credits")
  })

  it.each([
    "https://evil.example",
    "//evil.example/x",
    "javascript:alert(1)",
    "mailto:a@b.c",
    "/\\evil.example",
    "faq",
    "",
    null,
    42,
  ])("drops %s", (href) => {
    expect(inAppHref(href)).toBeNull()
  })
})

describe("linkPage", () => {
  it.each([
    ["/pricing", "pricing"],
    ["/top-up", "topUp"],
    ["/features", "features"],
    [`/companies/${COMPANY}/integrations/slack`, "slack"],
    [`/companies/${COMPANY}/integrations/greenhouse`, "integrations"],
    [`/companies/${COMPANY}/interviews/i1/candidates/c1`, "candidate"],
    [`/companies/${COMPANY}/interviews/i1/candidates`, "candidates"],
    [`/companies/${COMPANY}/interviews/i1`, "interview"],
    [`/companies/${COMPANY}/members`, "team"],
  ])("names %s", (href, page) => {
    expect(linkPage(href)).toBe(page)
  })

  it("names nothing for a page it doesn't know", () => {
    expect(linkPage("/somewhere")).toBeNull()
  })
})

describe("answerParts", () => {
  it("pairs each item with its page, and keeps link blocks' in-app pages", () => {
    const blocks: AssistantBlock[] = [
      { kind: "link", items: [], links: ["/settings"] },
      {
        kind: "candidate_rows",
        items: [{ email: "ann@example.com" }, { email: "bob@example.com" }],
        links: ["/companies/x/interviews/i/candidates/1", "https://evil"],
        all: "/companies/x/interviews/i?tab=candidates",
      },
      { kind: "link", items: [], links: ["/settings", "//evil", null] },
    ]

    expect(answerParts(blocks)).toEqual({
      rows: [
        {
          kind: "candidate_rows",
          items: [
            {
              item: { email: "ann@example.com" },
              href: "/companies/x/interviews/i/candidates/1",
            },
            { item: { email: "bob@example.com" }, href: null },
          ],
          // The page with all of the list, in-app only too.
          all: "/companies/x/interviews/i?tab=candidates",
        },
      ],
      // In-app pages only, as the service sent them.
      links: [
        { href: "/settings", label: null, page: null },
        { href: "/settings", label: null, page: null },
      ],
      signIn: undefined,
      cards: [],
    })
  })

  it("drops a list's page with all of it when it isn't in the app", () => {
    const blocks: AssistantBlock[] = [
      {
        kind: "interview",
        items: [{ title: "Analyst" }],
        links: ["/companies/x/interviews/i"],
        all: "https://evil",
      },
      { kind: "interview", items: [{ title: "Analyst" }], links: [null] },
    ]

    expect(answerParts(blocks).rows.map((row) => row.all)).toEqual([null, null])
  })

  it("keeps a sign-in card apart from the rows and links", () => {
    const card: AssistantBlock = {
      kind: "sign_in",
      items: [],
      links: [],
      provider: "github",
    }

    expect(answerParts([card])).toEqual({
      rows: [],
      links: [],
      signIn: card,
      cards: [],
    })
  })
})

describe("pageCompany", () => {
  it("reads the company from its pages, with or without a language", () => {
    expect(pageCompany(`/companies/${COMPANY}/interviews`)).toBe(COMPANY)
    expect(pageCompany(`/de/companies/${COMPANY}`)).toBe(COMPANY)
    expect(pageCompany("/companies")).toBeNull()
    expect(pageCompany("/pricing")).toBeNull()
  })
})

describe("transcribe", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn())
    vi.stubGlobal("document", { documentElement: { lang: "de" } })
  })

  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it("posts the recording as the body, in its format and the page's language", async () => {
    vi.mocked(fetch).mockResolvedValue(Response.json({ text: "Who passed?" }))
    const audio = new Blob(["opus"], { type: "audio/webm" })

    expect(await transcribe(audio)).toBe("Who passed?")
    const [url, init] = vi.mocked(fetch).mock.calls[0]
    expect(url).toBe("/api/assistant/transcribe")
    expect(init?.body).toBe(audio)
    expect(init?.headers).toMatchObject({
      "Content-Type": "audio/webm",
      "Accept-Language": "de",
    })
  })

  it("throws the service's message with its status", async () => {
    vi.mocked(fetch).mockResolvedValue(
      Response.json({ detail: "Couldn't hear anything." }, { status: 422 })
    )
    const failed = transcribe(new Blob([], { type: "audio/mp4" }))

    await expect(failed).rejects.toBeInstanceOf(ApiError)
    await expect(failed).rejects.toMatchObject({
      status: 422,
      message: "Couldn't hear anything.",
    })
  })
})

describe("withCard", () => {
  it("changes only the card with that action, wherever it is", () => {
    const card = (id: string): AssistantBlock => ({
      kind: "confirm",
      items: [],
      links: [],
      action_id: id,
      state: "pending",
    })
    const messages = [
      { role: "assistant" as const, content: "a", blocks: [card("a1")] },
      { role: "assistant" as const, content: "b", blocks: [card("a2")] },
    ]
    const changed = withCard(messages, "a2", { state: "done", links: ["/x"] })

    expect(changed[0].blocks[0].state).toBe("pending")
    expect(changed[1].blocks[0]).toMatchObject({ state: "done", links: ["/x"] })
  })
})

describe("withoutSignIn", () => {
  it("drops only the sign-in cards and keeps every message", () => {
    const messages = [
      { role: "user" as const, content: "Create a company", blocks: [] },
      {
        role: "assistant" as const,
        content: "Sign in below.",
        blocks: [
          { kind: "sign_in" as const, items: [], links: [] },
          { kind: "link" as const, items: [], links: ["/faq"] },
        ],
      },
    ]

    expect(withoutSignIn(messages)).toEqual([
      messages[0],
      {
        ...messages[1],
        blocks: [{ kind: "link", items: [], links: ["/faq"] }],
      },
    ])
  })
})

describe("withoutSecret", () => {
  it("empties and marks only the question being answered", () => {
    const messages = [
      { role: "user" as const, content: "Hi", blocks: [] },
      { role: "assistant" as const, content: "Hello", blocks: [] },
      { role: "user" as const, content: "my key pz_secret", blocks: [] },
      { role: "assistant" as const, content: "", blocks: [] },
    ]
    const cleaned = withoutSecret(messages)

    expect(cleaned[2]).toEqual({
      role: "user",
      content: "",
      blocks: [],
      removed: true,
    })
    expect(cleaned[0]).toEqual(messages[0])
    expect(JSON.stringify(cleaned)).not.toContain("pz_secret")
  })
})

describe("helpConversation", () => {
  it("sends a reply with the signature the help chat gave it", () => {
    expect(
      helpConversation([
        { role: "user", content: "How do I start?", blocks: [] },
        {
          role: "assistant",
          content: "Paste it.",
          blocks: [],
          signature: "abc",
        },
        { role: "assistant", content: "", blocks: [] },
      ])
    ).toEqual([
      { role: "user", content: "How do I start?" },
      { role: "assistant", content: "Paste it.", signature: "abc" },
    ])
  })
})

describe("answerHref", () => {
  it("keeps a link to a page the panel knows, by its path alone", () => {
    expect(answerHref("/companies/c1/interviews/i1")).toBe(
      "/companies/c1/interviews/i1"
    )
    expect(answerHref("/pricing#faq")).toBe("/pricing")
    expect(answerHref("/generate/g1?next=//evil.example")).toBe("/generate/g1")
  })

  it("drops a link to any other page, or off the site", () => {
    expect(answerHref("/connect?request=r1")).toBeNull()
    expect(answerHref("/join/token")).toBeNull()
    expect(answerHref("https://evil.example/pricing")).toBeNull()
    expect(answerHref("//evil.example/pricing")).toBeNull()
  })
})
