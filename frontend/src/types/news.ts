import type { components } from "@/types/api/library"

type Schemas = components["schemas"]

export type NewsPost = Schemas["NewsOut"]
export type AdminNewsPost = Schemas["AdminNewsOut"]
