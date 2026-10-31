// The features page's pictures of the real app, in public/features/<name>-<light|dark>.webp:
// made by e2e_tests/signed-in/specs/zz-features-shots.spec.ts (SHOTS=1) and
// scripts/features-shots.sh, which crops them and gives each its size here (both themes alike),
// at twice the pixels of the screen they were taken on.
export const FEATURE_SHOTS = {
  topics: { width: 1988, height: 1328 },
  invite: { width: 1024, height: 808 },
  settings: { width: 1988, height: 940 },
  start: { width: 2462, height: 1200 },
  question: { width: 2520, height: 960 },
  voice: { width: 2520, height: 1040 },
  brand: { width: 1988, height: 1400 },
  candidates: { width: 1988, height: 1328 },
  signals: { width: 2520, height: 1120 },
  share: { width: 1152, height: 584 },
  notes: { width: 1988, height: 840 },
  integrations: { width: 1988, height: 1400 },
  "bias-audit": { width: 1152, height: 1112 },
  email: { width: 1160, height: 1050 },
} as const

export type FeatureShotName = keyof typeof FEATURE_SHOTS

// Where the pictures are served from.
export const FEATURE_SHOTS_PATH = "/features"
