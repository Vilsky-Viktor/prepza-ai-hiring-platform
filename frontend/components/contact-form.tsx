"use client"

import { ForwardIcon } from "lucide-react"
import { useTranslations } from "next-intl"
import { useState } from "react"
import { toast } from "sonner"

import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import {
  MAX_CONTACT_MESSAGE_LENGTH,
  MAX_CONTACT_NAME_LENGTH,
  MAX_EMAIL_LENGTH,
} from "@/constants/limits"
import { useOneAtATime } from "@/hooks/use-one-at-a-time"
import { useHumanCheck } from "@/hooks/use-human-check"
import { apiErrorMessage, apiFetch } from "@/lib/api"
import { humanHeaders } from "@/lib/human-check"
import { isSubmitShortcut } from "@/lib/keys"

// No border, only a focus outline, like the chat inputs.
const BORDERLESS =
  "border-transparent focus-visible:border-ring focus-visible:ring-0"
const FIELD = `h-14 px-6 text-lg md:text-lg ${BORDERLESS}`

/** The contact page's form; the rounds service emails it to prepza's inbox. */
export function ContactForm() {
  const t = useTranslations("contact")
  useHumanCheck()
  const common = useTranslations("common")
  const [name, setName] = useState("")
  const [email, setEmail] = useState("")
  const [message, setMessage] = useState("")
  const [sending, setSending] = useState(false)
  // The address the reply goes to, once the message is sent.
  const [sentTo, setSentTo] = useState<string | null>(null)

  const once = useOneAtATime()

  async function send(event: React.FormEvent) {
    event.preventDefault()
    await once(async () => {
      setSending(true)

      try {
        await apiFetch("/rounds/help/contact", {
          method: "POST",
          body: JSON.stringify({ name, email, message }),
          headers: await humanHeaders(),
        })
        setSentTo(email.trim())
      } catch (error) {
        toast.error(apiErrorMessage(error, t("failed")))
      }

      setSending(false)
    })
  }

  if (sentTo) {
    return (
      <div role="status" className="space-y-2">
        <p className="font-heading text-3xl font-medium tracking-tight">
          {t("thanks")}
        </p>
        <p className="text-lg text-muted-foreground">
          {t("sent", { email: sentTo })}
        </p>
      </div>
    )
  }

  return (
    <form onSubmit={send} className="space-y-4">
      <div className="grid gap-4 sm:grid-cols-2">
        <Input
          required
          maxLength={MAX_CONTACT_NAME_LENGTH}
          autoComplete="name"
          placeholder={t("name")}
          aria-label={t("name")}
          value={name}
          onChange={(event) => setName(event.target.value)}
          className={FIELD}
        />
        <Input
          required
          type="email"
          maxLength={MAX_EMAIL_LENGTH}
          autoComplete="email"
          placeholder={t("email")}
          aria-label={t("email")}
          value={email}
          onChange={(event) => setEmail(event.target.value)}
          className={FIELD}
        />
      </div>
      <div className="relative">
        <Textarea
          required
          maxLength={MAX_CONTACT_MESSAGE_LENGTH}
          placeholder={t("messagePlaceholder")}
          aria-label={t("message")}
          value={message}
          onChange={(event) => setMessage(event.target.value)}
          onKeyDown={(event) => {
            if (isSubmitShortcut(event)) {
              event.preventDefault()
              event.currentTarget.form?.requestSubmit()
            }
          }}
          className={`min-h-48 resize-none rounded-[2rem] px-6 pt-4 pb-20 text-lg md:text-lg ${BORDERLESS}`}
        />
        <p className="pointer-events-none absolute start-6 bottom-6 text-xs text-muted-foreground pointer-coarse:hidden">
          {common("submitHint")}
        </p>
        <Button
          type="submit"
          size="icon-lg"
          className="absolute end-3 bottom-3 size-12 rounded-full"
          disabled={sending}
          aria-label={t("send")}
        >
          <ForwardIcon className="size-6 rtl:-scale-x-100" />
        </Button>
      </div>
    </form>
  )
}
