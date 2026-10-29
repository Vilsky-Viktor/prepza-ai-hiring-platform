import { useTranslations } from "next-intl"

import { AiAppsInstructions } from "@/components/common/ai-apps-setup"
import { Dotted } from "@/components/common/dot"
import { IntegrationRow } from "@/features/company/components/integration-row"
import { Badge } from "@/components/ui/badge"
import { MCP_MARK } from "@/config/ai-apps"
import { INTEGRATION_ACTIONS } from "@/config/lists"
import type { AiConnection } from "@/types/connections"

/** AI apps' row on the integrations tab: the MCP mark, the name, and which apps the user
 * connected, dot-separated ("connected" beside the name when any); the row opens their page, its Instructions
 * on top. */
export function AiAppsRow({
  companyId,
  connections,
}: {
  companyId: string
  connections: AiConnection[]
}) {
  const t = useTranslations("aiApps")
  const ats = useTranslations("ats")
  const names = [...new Set(connections.map((item) => item.client_name))]

  return (
    <IntegrationRow
      href={`/companies/${companyId}/integrations/ai`}
      logoClassName="p-7 max-sm:p-2.5"
      logo={
        // eslint-disable-next-line @next/next/no-img-element
        <img
          src={MCP_MARK}
          alt=""
          className="size-full object-contain dark:brightness-0 dark:invert"
        />
      }
      name={t("name")}
      status={
        names.length > 0 && (
          <Badge className="h-7 shrink-0 px-3 text-sm font-light">
            {ats("statusConnected")}
          </Badge>
        )
      }
      text={names.length > 0 ? <Dotted items={names} /> : t("rowText")}
      actions={
        <span className={INTEGRATION_ACTIONS}>
          <AiAppsInstructions />
        </span>
      }
    />
  )
}
