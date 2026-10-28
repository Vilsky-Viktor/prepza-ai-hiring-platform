"use client"

import { Markdown } from "@tiptap/markdown"
import { Placeholder } from "@tiptap/extensions"
import { EditorContent, useEditor, useEditorState } from "@tiptap/react"
import StarterKit from "@tiptap/starter-kit"
import {
  BoldIcon,
  ItalicIcon,
  LinkIcon,
  ListIcon,
  ListOrderedIcon,
} from "lucide-react"
import { useTranslations } from "next-intl"
import { useState } from "react"

import { IconButton } from "@/components/common/icon-button"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"

// Only what an email shows: bold, italic, links and lists.
const EXTENSIONS = (placeholder: string) => [
  StarterKit.configure({
    heading: false,
    blockquote: false,
    code: false,
    codeBlock: false,
    horizontalRule: false,
    strike: false,
    underline: false,
    link: { openOnClick: false, defaultProtocol: "https" },
  }),
  Markdown,
  Placeholder.configure({ placeholder }),
]

// The text as the email shows it: paragraphs apart, lists marked, links underlined.
const CONTENT =
  "min-h-48 px-6 py-4 text-lg outline-none wrap-anywhere [&_a]:text-primary [&_a]:underline [&_li]:my-1 [&_ol]:list-decimal [&_ol]:ps-6 [&_p:not(:first-child)]:mt-4 [&_p.is-editor-empty:first-child]:before:pointer-events-none [&_p.is-editor-empty:first-child]:before:float-start [&_p.is-editor-empty:first-child]:before:h-0 [&_p.is-editor-empty:first-child]:before:text-muted-foreground [&_p.is-editor-empty:first-child]:before:content-[attr(data-placeholder)] [&_ul]:list-disc [&_ul]:ps-6"

/** A text with a few styles, formatted as it's written: buttons (and Ctrl+B, Ctrl+I) for bold,
 * italic, a link and lists. `value` and `onChange` carry it as Markdown, as it's stored. */
export function TextEditor({
  value,
  onChange,
  label,
  placeholder,
}: {
  value: string
  onChange: (markdown: string) => void
  label: string
  placeholder: string
}) {
  const t = useTranslations("common")
  const [address, setAddress] = useState<string | null>(null)
  const editor = useEditor({
    extensions: EXTENSIONS(placeholder),
    content: value,
    contentType: "markdown",
    immediatelyRender: false,
    editorProps: {
      // What's typed takes its own direction (Arabic in an English page).
      attributes: {
        class: CONTENT,
        "aria-label": label,
        role: "textbox",
        dir: "auto",
      },
    },
    onUpdate: ({ editor }) => onChange(editor.getMarkdown()),
  })
  const on = useEditorState({
    editor,
    selector: ({ editor }) => ({
      bold: editor?.isActive("bold") ?? false,
      italic: editor?.isActive("italic") ?? false,
      link: editor?.isActive("link") ?? false,
      bullets: editor?.isActive("bulletList") ?? false,
      numbers: editor?.isActive("orderedList") ?? false,
    }),
  })

  const chain = () => editor!.chain().focus()

  function toggleLink() {
    if (on?.link) {
      chain().extendMarkRange("link").unsetLink().run()

      return
    }

    setAddress("")
  }

  function addLink() {
    const href = address?.trim()
    setAddress(null)

    if (!href) {
      return
    }

    // A link without selected words shows its address.
    if (editor!.state.selection.empty) {
      chain()
        .insertContent({
          type: "text",
          text: href,
          marks: [{ type: "link", attrs: { href } }],
        })
        .run()

      return
    }

    chain().extendMarkRange("link").setLink({ href }).run()
  }

  const tools = [
    {
      key: "bold",
      Icon: BoldIcon,
      pressed: on?.bold,
      run: () => chain().toggleBold().run(),
    },
    {
      key: "italic",
      Icon: ItalicIcon,
      pressed: on?.italic,
      run: () => chain().toggleItalic().run(),
    },
    { key: "link", Icon: LinkIcon, pressed: on?.link, run: toggleLink },
    {
      key: "bullets",
      Icon: ListIcon,
      pressed: on?.bullets,
      run: () => chain().toggleBulletList().run(),
    },
    {
      key: "numbers",
      Icon: ListOrderedIcon,
      pressed: on?.numbers,
      run: () => chain().toggleOrderedList().run(),
    },
  ] as const

  return (
    // The dialog's other fields' look: grey, without a border, outlined while focused.
    <div className="relative rounded-xl border border-transparent bg-surface transition-colors focus-within:border-ring-gradient">
      <div className="flex flex-wrap items-center gap-1 border-b border-background px-3 py-2 dark:border-border">
        {tools.map(({ key, Icon, pressed, run }) => (
          <IconButton
            key={key}
            label={t(`editor.${key}`)}
            pressed={pressed}
            disabled={!editor}
            onClick={run}
            className="size-9"
          >
            <Icon aria-hidden />
          </IconButton>
        ))}
      </div>
      {address !== null && (
        // The link's address, under the buttons; Enter adds it, Escape leaves it.
        <div className="flex items-center gap-2 border-b border-background px-3 py-2 dark:border-border">
          <Input
            autoFocus
            type="url"
            placeholder={t("editor.address")}
            aria-label={t("editor.address")}
            value={address}
            onChange={(event) => setAddress(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === "Enter") {
                event.preventDefault()
                addLink()
              }

              if (event.key === "Escape") {
                event.preventDefault()
                setAddress(null)
              }
            }}
            className="h-9 bg-background"
          />
          <Button type="button" className="h-9 px-4" onClick={addLink}>
            {t("editor.addLink")}
          </Button>
        </div>
      )}
      <EditorContent editor={editor} />
    </div>
  )
}
