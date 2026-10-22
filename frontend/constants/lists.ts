// Items a list asks the API for at a time; the next page loads as the user nears the end.
export const PAGE_SIZE = 20

// Start loading the next page when this many items are left below the viewport.
export const LOAD_AHEAD = 5

// Rows rendered beyond the viewport, so fast scrolling doesn't show blanks.
export const OVERSCAN = 6

// The viewport assumed before the browser can measure (server rendering), so the first rows
// render on the server instead of appearing only once the page's JavaScript runs.
export const INITIAL_VIEWPORT = { width: 1024, height: 1000 }

// A page's list: its rows in one bordered, rounded box. On phones it spans the screen, out of
// the page's side padding, with only its top and bottom borders and square corners.
export const LIST_BOX =
  "-mx-6 divide-y border-y sm:mx-0 sm:rounded-2xl sm:border"

/** An integration's row on the integrations tab: its logo tile, name and text, then its buttons.
 * On phones a small logo sits beside the name and the buttons take a full line under them. */
export const INTEGRATION_ROW =
  "relative flex items-center justify-between gap-6 py-6 pe-4 transition-colors hover:bg-muted/50 active:bg-muted/50 max-sm:grid max-sm:grid-cols-[3rem_minmax(0,1fr)] max-sm:gap-x-4 max-sm:gap-y-4 max-sm:px-4 sm:pe-6"

/** The row's link: it covers the whole row; on phones its logo and text join the row's grid. */
export const INTEGRATION_LINK =
  "flex min-w-0 items-center gap-4 self-stretch after:absolute after:inset-0 max-sm:contents"

/** The logo tile: full height of the row; on phones a small rounded tile beside the name. */
export const INTEGRATION_LOGO =
  "-my-6 me-2 flex min-h-[6.25rem] w-[6.25rem] shrink-0 items-center justify-center self-stretch overflow-hidden bg-muted max-sm:m-0 max-sm:size-12 max-sm:min-h-0 max-sm:self-start max-sm:rounded-lg"

/** An integration's group of buttons, on its row and on its page. */
export const INTEGRATION_ACTIONS = "flex shrink-0 items-center gap-3"
// A search as you type asks the service once typing pauses this long.
export const SEARCH_DELAY_MS = 300
// The public template catalog, the same for every visitor: its pages read it cached.
export const PUBLIC_TEMPLATES_PATH = "/library/templates"
