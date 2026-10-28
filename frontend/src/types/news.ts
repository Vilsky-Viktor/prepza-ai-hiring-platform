import type { components } from "@/types/api/site"

type Schemas = components["schemas"]

export type NewsPost = Schemas["NewsOut"]
export type AdminNewsPost = Schemas["AdminNewsOut"]
