// A field's name (components/ui/floating-field.tsx, the select pills): inside the box where the value
// goes while the field is empty, and a small pill on the box's top edge once it's focused or
// filled, shaped as the brand page's "Preview" pill on its preview's border.

// The grey box: the focus outline, the error border and the disabled look are the whole box's.
// Its top margin keeps room for the raised pill above it.
export const FLOAT_BOX =
  "relative mt-3 rounded-xl border border-transparent bg-surface transition-colors focus-within:border-ring has-disabled:cursor-not-allowed has-disabled:bg-input/50 has-disabled:opacity-50 has-aria-invalid:border-destructive dark:has-disabled:bg-input/80 dark:has-aria-invalid:border-destructive/50"

// `--pill`: a fill for something sitting on a grey field (the raised name, the description box's
// language picker), a mix of the muted grey and the page, a bit lighter than the field in both
// themes (still 4.5:1 for the muted text). Used with `bg-(--pill)`.
export const PILL_FILL =
  "[--pill:color-mix(in_oklch,var(--muted)_15%,var(--background))] dark:[--pill:color-mix(in_oklch,var(--muted)_85%,var(--background))]"

// Centred across the field, at rest and raised, so the pill stays clear of the rounding.
export const FLOAT_LABEL = `pointer-events-none absolute left-1/2 -translate-x-1/2 max-w-[calc(100%-2rem)] truncate rounded-full px-2 transition-all duration-200 ease-out ${PILL_FILL} motion-reduce:transition-none`

// Resting in a one-line field: centred, at the value's size and in the placeholders' colour.
export const FLOAT_LABEL_REST =
  "top-1/2 -translate-y-1/2 text-lg text-placeholder"

// Resting in a textarea: on its first line.
export const FLOAT_LABEL_REST_TOP =
  "top-4 translate-y-0 text-lg text-placeholder"

// Raised: a small pill astride the top edge, opaque over the edge's line.
export const FLOAT_LABEL_UP =
  "top-0 -translate-y-1/2 bg-(--pill) px-3 py-0.5 text-xs text-muted-foreground"

// Raised while the field before it (its `peer`) is focused, has a value or was autofilled.
export const FLOAT_LABEL_PEER_UP =
  "peer-focus:top-0 peer-focus:-translate-y-1/2 peer-focus:bg-(--pill) peer-focus:px-3 peer-focus:py-0.5 peer-focus:text-xs peer-focus:text-muted-foreground peer-not-placeholder-shown:top-0 peer-not-placeholder-shown:-translate-y-1/2 peer-not-placeholder-shown:bg-(--pill) peer-not-placeholder-shown:px-3 peer-not-placeholder-shown:py-0.5 peer-not-placeholder-shown:text-xs peer-not-placeholder-shown:text-muted-foreground peer-autofill:top-0 peer-autofill:-translate-y-1/2 peer-autofill:bg-(--pill) peer-autofill:px-3 peer-autofill:py-0.5 peer-autofill:text-xs peer-autofill:text-muted-foreground"

// The field itself, filling the box, its value centred. A hint placeholder shows only while the
// field is focused and empty (the label is up on the edge then); otherwise the label stands in.
export const FLOAT_FIELD =
  "peer w-full rounded-[inherit] border-0 bg-transparent px-6 text-lg shadow-none placeholder:text-transparent focus:placeholder:text-placeholder focus-visible:ring-0 disabled:bg-transparent disabled:opacity-100 aria-invalid:ring-0 md:text-lg dark:bg-transparent dark:disabled:bg-transparent"

// A unit or sign inside the field, at its start or end (px, s, %, $), muted; clicks go through
// to the field. Shown with the value, so it never sits beside the resting label.
export const FLOAT_ADORNMENT =
  "pointer-events-none absolute top-1/2 -translate-y-1/2 text-lg text-muted-foreground transition-opacity duration-200 motion-reduce:transition-none"

export const FLOAT_ADORNMENT_PEER_SHOWN =
  "opacity-0 peer-focus:opacity-100 peer-not-placeholder-shown:opacity-100 peer-autofill:opacity-100"

// Fields that always show something (a date's "dd/mm/yyyy"): their label is always raised.
export const ALWAYS_FILLED_TYPES = [
  "date",
  "time",
  "datetime-local",
  "month",
  "week",
]
