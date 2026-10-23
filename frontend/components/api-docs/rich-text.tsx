import Link from "next/link"

import { HighlightedCode } from "@/components/highlighted-code"
import { KeepAcronyms } from "@/components/keep-acronyms"
import { richText } from "@/lib/openapi"

type Section = ReturnType<typeof richText>[number]
type Pieces = Section["blocks"][number]["pieces"]

const TEXT = "text-base leading-relaxed text-muted-foreground"

/** A description from the API: its sections, the titled ones under a title like the page's
 * others ("## Keys"), with paragraphs and numbered steps. */
export function RichText({ text }: { text: string }) {
  return richText(text).map((section, index) =>
    section.title ? (
      <section key={index} className="space-y-6">
        <h2 className="font-heading text-2xl font-medium">
          <KeepAcronyms text={section.title} />
        </h2>
        <Blocks blocks={section.blocks} />
      </section>
    ) : (
      <Blocks key={index} blocks={section.blocks} />
    )
  )
}

function Blocks({ blocks }: { blocks: Section["blocks"] }) {
  return (
    <div className="space-y-4">
      {blocks.map((block, index) =>
        block.code !== undefined ? (
          <HighlightedCode key={index} variants={block.code} className="my-8" />
        ) : block.steps ? (
          <ol key={index} className={`list-decimal space-y-2 ps-5 ${TEXT}`}>
            {block.steps.map((step, at) => (
              <li key={at}>
                <Inline pieces={step} />
              </li>
            ))}
          </ol>
        ) : (
          <p key={index} className={TEXT}>
            <Inline pieces={block.pieces} />
          </p>
        )
      )}
    </div>
  )
}

function Inline({ pieces }: { pieces: Pieces }) {
  return pieces.map((piece, at) =>
    piece.kind === "bold" ? (
      <strong key={at} className="font-medium text-foreground">
        {piece.text}
      </strong>
    ) : piece.kind === "link" ? (
      <Link
        key={at}
        href={piece.href}
        className="text-foreground underline underline-offset-4"
      >
        {piece.text}
      </Link>
    ) : piece.kind === "code" ? (
      <code
        key={at}
        className="rounded-md bg-surface px-1.5 py-0.5 font-mono text-sm"
      >
        {piece.text}
      </code>
    ) : (
      piece.text
    )
  )
}
