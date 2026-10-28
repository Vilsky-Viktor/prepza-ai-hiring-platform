"use client"

import Link from "next/link"
import { useTranslations } from "next-intl"

import { Chips } from "@/components/company/ats-steps"
import { CopyValue } from "@/components/copy-field"
import { InstructionsDialog } from "@/components/instructions-dialog"
import {
  CHATGPT_AUTH,
  CHATGPT_CREATE,
  CHATGPT_DEVELOPER_PATH,
  CLAUDE_CONNECTOR_PATH,
  MCP_DOCS_PATH,
  MCP_NAME,
  MCP_PATH,
} from "@/constants/ai-apps"
import { useOrigin } from "@/lib/origin"

/** The MCP server's Instructions button, on its row and its page, like the other integrations':
 * a dialog with the server's address and the apps' steps, and a link to the developer docs for other apps and one's
 * own agents. */
export function AiAppsInstructions() {
  const t = useTranslations("aiApps")

  return (
    <InstructionsDialog title={t("instructionsTitle")}>
      <ServerAddress />
      <AppSteps />
      <p className="text-base text-muted-foreground">
        {t.rich("moreApps", {
          link: (chunks) => (
            <Link
              href={MCP_DOCS_PATH}
              className="text-foreground underline underline-offset-4"
            >
              {chunks}
            </Link>
          ),
        })}
      </p>
    </InstructionsDialog>
  )
}

/** The server's address to copy: in the dialog and on the developer docs' MCP tab. */
export function ServerAddress() {
  const t = useTranslations("aiApps")
  const ats = useTranslations("ats")
  const origin = useOrigin()

  return (
    <SetupSection title={t("serverTitle")} text={t("serverText")}>
      <CopyValue
        value={origin ? `${origin}${MCP_PATH}` : ""}
        label={ats("copyUrl")}
        copied={ats("copied")}
      />
    </SetupSection>
  )
}

/** Claude's steps and ChatGPT's, each under its title: in the dialog. */
export function AppSteps() {
  const t = useTranslations("aiApps")

  return (
    <>
      <SetupSection title={t.rich("addTo", { name: "Claude", app: KeepCase })}>
        <ClaudeSteps />
      </SetupSection>
      <SetupSection title={t.rich("addTo", { name: "ChatGPT", app: KeepCase })}>
        <ChatGptSteps />
      </SetupSection>
    </>
  )
}

/** Claude's steps and Claude Code's one command, in the ATS steps' style: in the dialog and on
 * the developer docs' MCP tab. */
export function ClaudeSteps() {
  const t = useTranslations("aiApps")
  const origin = useOrigin()
  const command = origin
    ? `claude mcp add --transport http ${MCP_NAME} ${origin}${MCP_PATH}`
    : ""

  return (
    <>
      <ol className="list-decimal space-y-3 ps-5 text-base text-muted-foreground">
        <li className="space-y-1.5">
          <span className="block">{t("claudeOpen")}</span>
          <Chips items={CLAUDE_CONNECTOR_PATH} path />
        </li>
        <li>{t("claudePaste", { name: MCP_NAME })}</li>
        <li>{t("allowOnPrepza")}</li>
      </ol>
      <div className="space-y-2">
        <p className="text-base text-muted-foreground">{t("claudeCode")}</p>
        <CopyValue
          value={command}
          label={t("copyCommand")}
          copied={t("commandCopied")}
        />
      </div>
    </>
  )
}

/** ChatGPT's steps: in the dialog and on the developer docs' MCP tab. */
export function ChatGptSteps() {
  const t = useTranslations("aiApps")

  return (
    <ol className="list-decimal space-y-3 ps-5 text-base text-muted-foreground">
      <li className="space-y-1.5">
        <span className="block">{t("chatgptDeveloper")}</span>
        <Chips items={CHATGPT_DEVELOPER_PATH} path />
      </li>
      <li className="space-y-1.5">
        <span className="block">{t("chatgptCreate")}</span>
        <Chips items={[CHATGPT_CREATE]} />
      </li>
      <li className="space-y-1.5">
        <span className="block">{t("chatgptPaste", { name: MCP_NAME })}</span>
        <Chips items={[CHATGPT_AUTH]} />
      </li>
      <li>{t("allowOnPrepza")}</li>
    </ol>
  )
}

/** A part of the setup: its title, what it's for when there's more to say, then its content.
 * The developer docs' other apps use it too. */
export function SetupSection({
  title,
  text,
  children,
}: {
  title: React.ReactNode
  text?: React.ReactNode
  children: React.ReactNode
}) {
  return (
    <section className="space-y-4">
      <div className="space-y-1">
        <h3 className="text-lg font-medium">{title}</h3>
        {text && <p className="text-base text-muted-foreground">{text}</p>}
      </div>
      {children}
    </section>
  )
}

/** An app's name in a lowercase title, keeping its own capitals. */
function KeepCase(chunks: React.ReactNode) {
  return <span className="normal-case">{chunks}</span>
}
