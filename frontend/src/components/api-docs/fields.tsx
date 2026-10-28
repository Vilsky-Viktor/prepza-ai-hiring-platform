import { getTranslations } from "next-intl/server"

import { refName } from "@/lib/openapi"
import type { Field } from "@/types/openapi"
import { LIST_BOX } from "@/constants/lists"

/** Fields in one list like the site's others: each name, its type (an object's links to it),
 * whether it's required and what it is. */
export async function Fields({ fields }: { fields: Field[] }) {
  const t = await getTranslations("apiDocs")

  return (
    <ul className={LIST_BOX}>
      {fields.map((field) => (
        <li key={field.name} className="space-y-1 px-5 py-4">
          <p className="flex flex-wrap items-baseline gap-x-3 gap-y-1">
            <code className="font-mono text-base font-medium">
              {field.name}
            </code>
            <TypeName type={field.type} />
            {field.required && (
              <span className="text-sm text-primary">{t("required")}</span>
            )}
          </p>
          {field.description && (
            <p className="text-sm text-muted-foreground">{field.description}</p>
          )}
        </li>
      ))}
    </ul>
  )
}

/** A type, its object names linked to their place under Objects. */
export function TypeName({ type }: { type: string }) {
  return (
    <span className="font-mono text-sm text-muted-foreground">
      {type.split(/([A-Z][A-Za-z]+)/).map((piece, index) =>
        /^[A-Z]/.test(piece) ? (
          <a
            key={index}
            href={`/api-docs?tab=objects#${refName(piece)}`}
            className="underline underline-offset-4 hover:text-foreground"
          >
            {piece}
          </a>
        ) : (
          piece
        )
      )}
    </span>
  )
}
