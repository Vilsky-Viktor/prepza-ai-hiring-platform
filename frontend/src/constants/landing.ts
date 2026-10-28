// The pass mark of the home page's sample test, the same as a new test's default (the companies
// service's DEFAULT_PASS_MARK).
export const DEMO_PASS_MARK = 70

// Where "watch demos" on the home page leads: prepza's demo videos on YouTube.
export const DEMOS_URL = "https://www.youtube.com/@prepza"
// The YouTube video the hero's "video" button plays; a stand-in until prepza's own is up.
export const HERO_VIDEO_ID = "aqz-KE-bpKQ"

// How long a full interview takes from a job description to ready, rounded up for a safe promise
// (a 7-topic, hard template took about 7 minutes on 2026-10-17); shown under the home page's box.
export const READY_MINUTES = 10

// The hero's wires: five on the left of the job description box, each from the window's edge
// (x 0) to the box (x 100, in percent of the width). A curve is its start height and two bends
// (each a point the curve leans toward, as x and y), in units of WIRE_UNIT pixels around the box's
// middle (50 is the middle), and where it meets the box: steps of WIRE_GAP pixels from the middle.
// So the wires look the same and stay centred on the box at any box height. Fixed, so every
// visit draws the same curves.
export const HERO_WIRES = [
  {
    from: -160,
    bends: [
      [30, -110],
      [65, 5],
    ],
    to: -2,
    delay: 0,
  },
  {
    from: -45,
    bends: [
      [40, -20],
      [70, 35],
    ],
    to: -1,
    delay: 1.3,
  },
  {
    from: 55,
    bends: [
      [25, 75],
      [60, 40],
    ],
    to: 0,
    delay: 0.5,
  },
  {
    from: 150,
    bends: [
      [35, 125],
      [75, 75],
    ],
    to: 1,
    delay: 1.9,
  },
  {
    from: 255,
    bends: [
      [45, 210],
      [65, 100],
    ],
    to: 2,
    delay: 0.9,
  },
] as const

// The distance between two wires where they meet the box, in pixels.
export const WIRE_GAP = 30

// Pixels per unit of a wire's heights.
export const WIRE_UNIT = 1.5

// How fast a spark runs along its wire, in pixels a second, the same on every screen; and how
// fast it pulses, in seconds.
export const SPARK_SPEED = 170
export const PULSE_SECONDS = 0.6

// The hero's right side: one straight wire out of the box, its candidates this many times the
// left's size, running at this speed in pixels a second (slower than the left's).
export const OUT_SIZE = 1.5
export const OUT_SPEED = 120

// How much thicker the right side's wire is than the left's.
export const OUT_THICKNESS = 2
