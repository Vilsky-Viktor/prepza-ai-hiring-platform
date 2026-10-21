// The landing's sample reports: a ZIP of the two PDF reports made from made-up data
// (scripts/report-samples.sh makes it again when the reports' design changes).
export const REPORT_SAMPLES_URL = "/samples/prepza-report-samples.zip"

// Cached for a day, like the logos: the file changes only when the samples are made again.
export const REPORT_SAMPLES_HEADERS = [
  { key: "Cache-Control", value: "public, max-age=86400" },
]
