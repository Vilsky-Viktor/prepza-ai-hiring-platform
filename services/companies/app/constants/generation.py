# The generation service's answers passed on to the client as it said them: gone (404), the
# wrong state (409), invalid (422), a limit such as its per-person one or a topic's revisions
# (429), and the day's AI budget or a pause (503), each with its Retry-After.
GENERATION_REFUSALS = {404, 409, 422, 429, 503}
