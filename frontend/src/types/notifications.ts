import type { components } from "@/types/api/notifications"

type Schemas = components["schemas"]

export type NotificationFeed = Schemas["FeedOut"]
export type AppNotification = Schemas["NotificationOut"]
export type SlackOverview = Schemas["SlackOut"]
export type UnsubscribeLink = Schemas["UnsubscribeOut"]
