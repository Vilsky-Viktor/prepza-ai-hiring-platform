// A field's name (components/ui/floating-field.tsx, the select pills): a small pill centred on the
// box's top edge, always, shaped as the brand page's "Preview" pill on its preview's border; the
// field's placeholder shows inside it, from the start.

// The grey box: the focus outline, the error border and the disabled look are the whole box's,
// the disabled look only when the field is (a disabled button in it, "Save", leaves the field
// as it is). Its top margin keeps room for the raised pill above it.
export const FLOAT_BOX =
  "relative mt-3 rounded-xl border border-transparent bg-surface transition-colors focus-within:border-ring-gradient has-[:is(input,textarea):disabled]:cursor-not-allowed has-[:is(input,textarea):disabled]:bg-input/50 has-[:is(input,textarea):disabled]:opacity-50 has-aria-invalid:border-destructive has-aria-invalid:before:hidden dark:has-[:is(input,textarea):disabled]:bg-input/80 dark:has-aria-invalid:border-destructive/50"

// `--pill`: a fill for something sitting on a grey field (the raised name, the description box's
// language picker), a mix of the muted grey and the page, a bit lighter than the field in both
// themes (still 4.5:1 for the muted text). Used with `bg-(--pill)`.
export const PILL_FILL =
  "[--pill:color-mix(in_oklch,var(--muted)_15%,var(--background))] dark:[--pill:color-mix(in_oklch,var(--muted)_85%,var(--background))]"

// Centred across the field, at rest and raised, so the pill stays clear of the rounding.
export const FLOAT_LABEL = `pointer-events-none absolute left-1/2 -translate-x-1/2 max-w-[calc(100%-2rem)] truncate rounded-full px-2 transition-all duration-200 ease-out ${PILL_FILL} motion-reduce:transition-none`

// Resting in a one-line select with nothing chosen (the menu pills): centred, at the value's size
// and in the placeholders' colour.
export const FLOAT_LABEL_REST =
  "top-1/2 -translate-y-1/2 text-lg text-placeholder"

// Raised: a small pill astride the top edge, opaque over the edge's line.
export const FLOAT_LABEL_UP =
  "top-0 -translate-y-1/2 bg-(--pill) px-3 py-0.5 text-xs text-muted-foreground"

// The field itself, filling the box, its value and placeholder from the start.
export const FLOAT_FIELD =
  "peer w-full rounded-[inherit] border-0 bg-transparent px-6 text-lg shadow-none placeholder:text-placeholder focus-visible:ring-0 disabled:bg-transparent disabled:opacity-100 aria-invalid:ring-0 md:text-lg dark:bg-transparent dark:disabled:bg-transparent"

// A unit or sign inside the field, at its start or end (px, s, %, $), muted; clicks go through
// to the field.
export const FLOAT_ADORNMENT =
  "pointer-events-none absolute top-1/2 -translate-y-1/2 text-lg text-muted-foreground transition-opacity duration-200 motion-reduce:transition-none"
