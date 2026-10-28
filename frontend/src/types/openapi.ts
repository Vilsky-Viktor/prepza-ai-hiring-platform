// The parts of an OpenAPI 3.1 description the API docs page reads.
export type Schema = {
  $ref?: string
  type?: string
  format?: string
  title?: string
  description?: string
  items?: Schema
  anyOf?: Schema[]
  properties?: Record<string, Schema>
  required?: string[]
  default?: unknown
  maximum?: number
  minimum?: number
}

export type Parameter = {
  name: string
  in: string
  required?: boolean
  description?: string
  schema: Schema
}

export type Operation = {
  summary?: string
  description?: string
  tags?: string[]
  parameters?: Parameter[]
  requestBody?: { content: Record<string, { schema: Schema }> }
  responses: Record<
    string,
    { description: string; content?: Record<string, { schema: Schema }> }
  >
}

export type OpenApi = {
  info: { title: string; version: string; description?: string }
  servers?: { url: string }[]
  paths: Record<string, Record<string, Operation>>
  webhooks?: Record<string, Record<string, Operation>>
  components: { schemas: Record<string, Schema> }
}

export type Field = {
  name: string
  type: string
  required: boolean
  description: string
}
