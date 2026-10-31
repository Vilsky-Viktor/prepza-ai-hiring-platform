import {
  ArrowLeftRightIcon,
  BadgeCheckIcon,
  BellIcon,
  BotMessageSquareIcon,
  CalendarClockIcon,
  CodeXmlIcon,
  CoinsIcon,
  EarthIcon,
  EyeIcon,
  FileTextIcon,
  GiftIcon,
  HandshakeIcon,
  HistoryIcon,
  LanguagesIcon,
  LayoutTemplateIcon,
  LibraryIcon,
  PersonStandingIcon,
  RefreshCwIcon,
  ScaleIcon,
  ShieldCheckIcon,
  SparklesIcon,
  ThumbsUpIcon,
  TimerIcon,
  UserCheckIcon,
  UserSearchIcon,
  UsersIcon,
  WebhookIcon,
  type LucideIcon,
} from "lucide-react"
import type { ComponentType } from "react"

import { McpIcon } from "@/components/icons/mcp-icon"
import { BAND } from "@/config/landing-backgrounds"
import type { FeatureShotName } from "@/config/features-shots"
import type {
  FeatureCardKey,
  FeatureGroupId,
  FeatureMoreKey,
  FeaturePointKey,
  FeatureRowKey,
} from "@/types/features-page"

// The features page (app/features/page.tsx): its groups in order, each a landing section with
// its in-page link, rows of a text beside a picture of the real app, and small cards under them.
// Texts are "featuresPage.rows.<key>" and "featuresPage.cards.<key>"; a row's points are its
// "points.<point>" messages.

export type FeatureRow = {
  key: FeatureRowKey
  shot: FeatureShotName
  points: readonly FeaturePointKey[]
  // Logos under the text: the ATSs'.
  logos?: "ats"
}

export type FeatureCard = {
  key: FeatureCardKey
  icon: LucideIcon | ComponentType<{ className?: string }>
}

export type FeatureGroup = {
  id: FeatureGroupId
  // A grey band across the window behind it (config/landing-backgrounds.ts), or none.
  background?: string
  rows: readonly FeatureRow[]
  cards: readonly FeatureCard[]
  // A link onwards under the cards: where, and its "featuresPage.more.<key>" label.
  more?: { href: string; key: FeatureMoreKey }
}

export const FEATURE_GROUPS: readonly FeatureGroup[] = [
  {
    id: "create",
    background: BAND,
    rows: [
      {
        key: "describe",
        shot: "topics",
        points: ["questions", "options", "examples"],
      },
    ],
    cards: [
      { key: "templates", icon: LayoutTemplateIcon },
      { key: "bank", icon: LibraryIcon },
      { key: "quality", icon: RefreshCwIcon },
      { key: "languages", icon: LanguagesIcon },
      { key: "preview", icon: EyeIcon },
    ],
  },
  {
    id: "invite",
    rows: [
      { key: "invite", shot: "invite", points: ["names", "credits", "expire"] },
      {
        key: "link",
        shot: "settings",
        points: ["linkOff", "mode", "settings"],
      },
    ],
    cards: [
      { key: "ats", icon: ArrowLeftRightIcon },
      { key: "platform", icon: CodeXmlIcon },
      { key: "assistants", icon: BotMessageSquareIcon },
    ],
  },
  {
    id: "interview",
    background: BAND,
    rows: [
      { key: "start", shot: "start", points: ["askTime", "peopleDecide"] },
      { key: "click", shot: "question", points: ["time", "phone", "saved"] },
      {
        key: "voice",
        shot: "voice",
        points: ["tap", "kept", "voiceLanguages"],
      },
      { key: "brand", shot: "brand", points: ["contrast", "logo"] },
    ],
    cards: [
      { key: "extraTime", icon: TimerIcon },
      { key: "ownMode", icon: ArrowLeftRightIcon },
      { key: "fair", icon: ScaleIcon },
      { key: "rate", icon: ThumbsUpIcon },
      { key: "accessible", icon: PersonStandingIcon },
    ],
  },
  {
    id: "decide",
    rows: [
      { key: "candidates", shot: "candidates", points: ["sort", "status"] },
      {
        key: "signals",
        shot: "signals",
        points: ["proof", "camera", "followUps"],
      },
      {
        key: "share",
        shot: "share",
        points: ["pdf", "messengers", "viewers"],
      },
      { key: "notes", shot: "notes", points: ["everyone", "bell"] },
      {
        key: "emails",
        shot: "email",
        points: ["digest", "emailChoice", "stopEmails"],
      },
    ],
    cards: [
      { key: "notifications", icon: BellIcon },
      { key: "discover", icon: UserSearchIcon },
      { key: "hired", icon: CalendarClockIcon },
    ],
  },
  {
    id: "connect",
    background: BAND,
    rows: [
      {
        key: "integrations",
        shot: "integrations",
        points: ["atsList", "results", "docs"],
        logos: "ats",
      },
    ],
    cards: [
      { key: "mira", icon: SparklesIcon },
      { key: "mcp", icon: McpIcon },
      { key: "api", icon: CodeXmlIcon },
      { key: "webhooks", icon: WebhookIcon },
      { key: "slack", icon: BellIcon },
    ],
    more: { href: "/api-docs", key: "developerDocs" },
  },
  {
    id: "trust",
    rows: [
      {
        key: "biasAudit",
        shot: "bias-audit",
        points: ["noInference", "owner"],
      },
    ],
    cards: [
      { key: "person", icon: UserCheckIcon },
      { key: "roles", icon: UsersIcon },
      { key: "log", icon: HistoryIcon },
      { key: "documents", icon: FileTextIcon },
      { key: "privacy", icon: ShieldCheckIcon },
      { key: "verified", icon: BadgeCheckIcon },
    ],
    more: { href: "/trust", key: "trust" },
  },
  {
    id: "pricing",
    background: BAND,
    rows: [],
    cards: [
      { key: "free", icon: GiftIcon },
      { key: "answered", icon: UserCheckIcon },
      { key: "expire", icon: CoinsIcon },
      { key: "autoTopUp", icon: RefreshCwIcon },
      { key: "referrals", icon: HandshakeIcon },
      { key: "currencies", icon: EarthIcon },
    ],
    more: { href: "/pricing", key: "pricing" },
  },
]
