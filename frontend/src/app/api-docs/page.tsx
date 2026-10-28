import { notFound } from "next/navigation"
import { getLocale, getTranslations } from "next-intl/server"

import { DocSection } from "@/components/api-docs/doc-section"
import { Fields } from "@/components/api-docs/fields"
import {
  McpAgents,
  McpApp,
  McpTab,
  McpToolList,
} from "@/components/api-docs/mcp-tab"
import { Operation } from "@/components/api-docs/operation"
import { RichText } from "@/components/api-docs/rich-text"
import { CopyValue } from "@/components/common/copy-field"
import { DocsMenu } from "@/components/api-docs/docs-menu"
import { JsonLd } from "@/components/common/json-ld"
import { DOC_TABS } from "@/config/api-docs"
import { DEFAULT_LOCALE } from "@/config/i18n"
import { MCP_APP_PAGES, MCP_SUB_PAGES, MCP_TOOLS_PATH } from "@/config/mcp-docs"
import { mcpExamples } from "@/lib/mcp-examples"
import {
  descriptionTabs,
  fieldsOf,
  operationsOf,
  schemasOf,
} from "@/lib/openapi"
import { publicFetch } from "@/lib/server-api"
import { pageMetadata, previewImage, siteUrl } from "@/lib/site"
import { breadcrumbData, techArticleData } from "@/lib/structured-data"
import type { McpTools } from "@/types/mcp"
import type { OpenApi } from "@/types/openapi"
import { PageKey } from "@/components/common/page-key"

export async function generateMetadata() {
  const t = await getTranslations("apiDocs")

  return pageMetadata(t("title"), t("description"), "/api-docs")
}

/** The developer docs, read from the API's own description, so they always match it: a tab for
 * the API (how to sign in, its routes), its web hooks, the SDK that embeds the interview, the
 * MCP server (its tools and limits read from the server; its longer parts and each AI app's
 * setup pages of its own, `page`), and the objects they return. English only, like the legal pages. */
export default async function ApiDocsPage({
  searchParams,
}: {
  searchParams: Promise<{ tab?: string; page?: string }>
}) {
  const t = await getTranslations("apiDocs")
  const locale = await getLocale()
  const { tab, page: asked } = await searchParams
  const current = DOC_TABS.find((item) => item === tab) ?? "api"
  // A page of the MCP tab; any other address on it is the tab's overview.
  const mcpPage = MCP_SUB_PAGES.find(
    (item) => current === "mcp" && item.id === asked
  )?.id
  const spec = await publicFetch<OpenApi>("/v1/openapi.json", { locale: "en" })

  if (!spec) {
    notFound()
  }

  const texts = descriptionTabs(spec.info.description ?? "")
  // The MCP tab's own pages: its overview, then the rest, the apps by their own names.
  const mcpPages = [
    {
      id: "overview",
      href: "/api-docs?tab=mcp",
      label: t("mcpPages.overview"),
    },
    ...MCP_SUB_PAGES.map((page) => ({
      ...page,
      label: "label" in page ? page.label : t(`mcpPages.${page.id}`),
    })),
  ]
  const tabs = DOC_TABS.map((id) => ({
    id,
    href: id === "api" ? "/api-docs" : `/api-docs?tab=${id}`,
    label: id === "objects" ? t("objects") : t(`tabs.${id}`),
    // Acronyms keep their capitals in the lowercase tabs.
    keepCase: id === "api" || id === "sdk" || id === "mcp",
    sub: id === "mcp" ? mcpPages : undefined,
  }))

  const site = siteUrl()

  return (
    <main className="mx-auto max-w-page space-y-12 px-6 py-12">
      <PageKey page="apiDocs" />
      <JsonLd
        data={[
          techArticleData(site, {
            title: t("title"),
            description: t("description"),
            path: "/api-docs",
            image: previewImage(t("title"))[0].url,
          }),
          breadcrumbData(site, [
            { name: "prepza", path: "/" },
            { name: t("title"), path: "/api-docs" },
          ]),
        ]}
      />
      <header className="space-y-4">
        <h1 className="font-heading text-4xl font-medium tracking-tight">
          {t("title")}
        </h1>
        {locale !== DEFAULT_LOCALE && (
          <p className="text-sm text-muted-foreground">{t("englishOnly")}</p>
        )}
      </header>
      <DocsMenu
        tabs={tabs}
        current={current}
        currentSub={mcpPage ?? "overview"}
      >
        <div lang="en" dir="ltr" className="space-y-12">
          {current === "api" && <ApiTab spec={spec} text={texts.api} />}
          {current === "webhooks" && (
            <WebhooksTab spec={spec} text={texts.webhooks} />
          )}
          {current === "sdk" && texts.sdk && <RichText text={texts.sdk} />}
          {current === "mcp" && <McpPage page={mcpPage} site={site} />}
          {current === "objects" &&
            schemasOf(spec).map(([name, schema]) => (
              <article key={name} id={name} className="scroll-mt-20 space-y-3">
                <h3 className="font-mono text-xl font-medium normal-case">
                  {name}
                </h3>
                {schema.description && <RichText text={schema.description} />}
                <Fields fields={fieldsOf(spec, schema)} />
              </article>
            ))}
        </div>
      </DocsMenu>
    </main>
  )
}

/** The MCP tab's open page: the example agents, an AI app's setup, or a page with what it shows
 * from the server (the tools, or the overview with the limits in its rules). */
async function McpPage({ page, site }: { page?: string; site: string }) {
  if (page === "frameworks") {
    return <McpAgents examples={await mcpExamples()} />
  }

  if (MCP_APP_PAGES.some((item) => item.id === page)) {
    return <McpApp site={site} app={page ?? ""} />
  }

  const tools = await publicFetch<McpTools>(MCP_TOOLS_PATH, { locale: "en" })

  if (page === "tools") {
    return tools && <McpToolList tools={tools} />
  }

  return <McpTab tools={tools} />
}

/** The API tab: how to sign in (the description's text), the base URL and every route. */
async function ApiTab({ spec, text }: { spec: OpenApi; text?: string }) {
  const t = await getTranslations("apiDocs")

  return (
    <>
      {text && <RichText text={text} />}
      <DocSection title={t("baseUrl")}>
        <CopyValue
          value={spec.servers?.[0]?.url ?? ""}
          label={t("copyBaseUrl")}
          copied={t("baseUrlCopied")}
        />
      </DocSection>
      <DocSection title={t("endpoints")}>
        {operationsOf(spec.paths).map((item) => (
          <Operation
            key={`${item.method} ${item.path}`}
            spec={spec}
            {...item}
          />
        ))}
      </DocSection>
    </>
  )
}

/** The web hooks tab: the description's text and each web hook. */
async function WebhooksTab({ spec, text }: { spec: OpenApi; text?: string }) {
  const t = await getTranslations("apiDocs")

  return (
    <>
      {text && <RichText text={text} />}
      {spec.webhooks && (
        <DocSection title={t("webhooks")}>
          {operationsOf(spec.webhooks).map((item) => (
            <Operation key={item.path} spec={spec} {...item} />
          ))}
        </DocSection>
      )}
    </>
  )
}
