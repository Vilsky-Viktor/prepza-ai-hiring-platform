import { getTranslations } from "next-intl/server"

import { Fields, TypeName } from "@/components/api-docs/fields"
import { RichText } from "@/components/api-docs/rich-text"
import { Badge } from "@/components/ui/badge"
import {
  bodySchema,
  errorsOf,
  fieldsOf,
  successSchema,
  typeOf,
} from "@/lib/openapi"
import type { OpenApi, Operation as OperationSpec } from "@/types/openapi"
import { CARD } from "@/constants/cards"

/** One route (or web hook): its method and path, what it does, what it takes, what it returns
 * and the errors it may answer with. */
export async function Operation({
  spec,
  method,
  path,
  operation,
}: {
  spec: OpenApi
  method: string
  path: string
  operation: OperationSpec
}) {
  const t = await getTranslations("apiDocs")
  const parameters = (operation.parameters ?? []).map((parameter) => ({
    name: parameter.name,
    type: `${typeOf(parameter.schema)}, ${parameter.in}`,
    required: parameter.required ?? false,
    description: parameter.description ?? "",
  }))
  const body = bodySchema(operation)
  const returns = successSchema(operation)
  const errors = errorsOf(operation)

  return (
    <article className={`space-y-5 ${CARD}`}>
      <header className="space-y-3">
        <h3 className="text-xl font-medium">{operation.summary}</h3>
        <p className="flex flex-wrap items-center gap-3">
          <Badge
            variant="secondary"
            className="h-7 px-3 font-mono text-sm normal-case"
          >
            {method}
          </Badge>
          <code className="font-mono text-base break-all">{path}</code>
        </p>
      </header>
      {operation.description && <RichText text={operation.description} />}
      {parameters.length > 0 && (
        <Part title={t("parameters")}>
          <Fields fields={parameters} />
        </Part>
      )}
      {body && (
        <Part title={t("body")}>
          <Fields fields={fieldsOf(spec, body)} />
        </Part>
      )}
      {returns && Object.keys(returns).length > 0 && (
        <Part title={t("returns")}>
          <TypeName type={typeOf(returns)} />
        </Part>
      )}
      {errors.length > 0 && (
        <Part title={t("errors")}>
          <ul className="space-y-1 text-sm text-muted-foreground">
            {errors.map((error) => (
              <li key={error.code}>
                <code className="font-mono font-medium text-foreground">
                  {error.code}
                </code>{" "}
                {error.description}
              </li>
            ))}
          </ul>
        </Part>
      )}
    </article>
  )
}

function Part({
  title,
  children,
}: {
  title: string
  children: React.ReactNode
}) {
  return (
    <section className="space-y-2">
      <h4 className="text-sm font-medium text-muted-foreground">{title}</h4>
      {children}
    </section>
  )
}
