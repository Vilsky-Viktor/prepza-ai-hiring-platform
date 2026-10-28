import type { components } from "@/types/api/generation"

type Schemas = components["schemas"]

export type Generation = Schemas["GenerationOut"]
export type GenerationStatus = Generation["status"]
export type DraftTopic = Schemas["DraftTopic"]
/** A template's latest question addition and the numbers a superadmin's addition may ask for. */
export type Addition = Schemas["AdditionOut"]
/** A recurring mistake the weekly job proposed, on the admin zone's patterns tab. */
export type QualityPattern = Schemas["PatternOut"]
/** How big a new interview is made (questions per topic), as set in Controls. */
export type Sizes = Schemas["SizesOut"]
