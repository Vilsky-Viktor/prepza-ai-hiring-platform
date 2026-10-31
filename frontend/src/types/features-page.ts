import type en from "../../messages/en.json"

// The features page's message keys, so its config names only texts that exist.
type Texts = (typeof en)["featuresPage"]

export type FeatureGroupId = keyof Texts["groups"]
export type FeatureRowKey = keyof Texts["rows"]
export type FeaturePointKey = keyof Texts["points"]
export type FeatureCardKey = keyof Texts["cards"]
export type FeatureMoreKey = keyof Texts["more"]
