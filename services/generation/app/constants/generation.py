from typing import Literal

from prepza_common.constants import MAX_GOAL_LENGTH  # noqa: F401 (re-exported)

# How many AI calls one generation makes at once, and how many a second all of them together,
# are set in the admin zone's Controls tab (GENERATION_CALLS_AT_ONCE, GENERATION_CALLS_PER_SECOND).
RECURSION_LIMIT = 200

# A topic's or subtopic's name, drafted or edited by hand during review. How many topics and
# subtopics a test has, and its questions per topic, are set in the admin zone's Controls tab
# (MAX_TOPICS, MAX_SUBTOPICS, INTERVIEW_QUESTIONS_PER_TOPIC, TEMPLATE_QUESTIONS_PER_TOPIC).
MAX_TOPIC_NAME_LENGTH = 50
TOPIC_ATTEMPTS = 2
# Questions are written for this many times a topic's size, to replace the ones dropped as
# ambiguous or duplicate. 1.0 since testing (evals/README.md): rounding each subtopic's count up
# left enough spares, and fill_topics covers whatever is still missing.
QUESTION_OVERSAMPLE = 1.0
# Questions, each with its options, per call. A subtopic needing more is split into calls.
QUESTION_BATCH_SIZE = 20
# Each call for the same subtopic takes the next angle, so parallel calls don't write the same
# obvious questions.
QUESTION_FOCUSES = (
    "core concepts: what they mean in practice and how they differ",
    "applying it to a concrete case: working out the result or choosing the right approach",
    "situations: what happens next, what went wrong, or what to do first",
    "trade-offs, edge cases and common mistakes",
)
# Questions whose embeddings are this close (cosine distance) ask the same thing in other words.
DUPLICATE_DISTANCE = 0.08
ANSWER_ATTEMPTS = 3
QUESTION_ATTEMPTS = 3
# Output cap per call, reasoning tokens included. A model that loops fails at this many tokens
# instead of writing until its own limit, minutes later.
MAX_OUTPUT_TOKENS = 16_000
# Writing MAX_OUTPUT_TOKENS can take a few minutes; a call silent for longer has hung.
LLM_TIMEOUT_SECONDS = 300
# Retries of a failed AI call: quick failures (a rate limit, a dropped connection) recover, and a
# stuck call gives up after at most (1 + this) * LLM_TIMEOUT_SECONDS, within a run's time.
LLM_MAX_RETRIES = 2
# The Batch API's calls aren't retried by OpenAI's client: creating a file or a batch carries no
# idempotency key, so a retry after a lost answer would make (and bill) a second batch. The next
# scheduled run sends what didn't go and reads what wasn't read.
BATCH_MAX_RETRIES = 0
# What OpenAI accepts for a reasoning model's effort; the settings pick one (see config).
ReasoningEffort = Literal["none", "minimal", "low", "medium", "high"]
# Every question has this many options: one correct, or for a multi-answer ("select all that
# apply") question 2 or 3 of them, never all (prepza_common.multi_answer).
MAX_MULTI_CORRECT = 3
OPTIONS = 4
# A question, its example and its four options are read and answered within a minute, also by
# someone reading in a language that isn't their own (prompts/question_rules.py READING_RULES).
# The prompts ask for less; these catch what went far over, and the question is dropped.
# Any answer option:
MAX_OPTION_CHARS = 100
# The question's sentences, without its example:
MAX_QUESTION_CHARS = 400
# Its example's lines:
MAX_EXAMPLE_LINES = 10
REGENERATE_ATTEMPTS = 3
# Writing a regenerated question must finish within this, so the whole request (reading the
# question, up to 15 s; writing; saving the new one, up to 15 s; recording its AI usage, up to 5 s
# a model) ends within the 140 s companies waits for it (REGENERATE_CALL_SECONDS); past it nothing
# is replaced, so a company that tries again never gets two replacements.
REGENERATE_TIMEOUT_SECONDS = 90
# Rounds of extra questions for a topic that ended short, before the generation fails.
FILL_ATTEMPTS = 3
# Extra questions a fill-up asks for beyond what's missing: it runs one round after another, so a
# spare saves a round when one comes back a duplicate.
FILL_SPARE_QUESTIONS = 2

# The changes a reviewer describes in words during topic review; how many times one
# generation's topics may be revised that way is the MAX_TOPIC_REVISIONS limit.
MAX_INSTRUCTIONS_LENGTH = 500
TOO_MANY_REVISIONS = "These topics can't be changed in words any more. Choose the topics to keep."
# A review approving more topics than MAX_TOPICS, or a topic edited with more subtopics than
# MAX_SUBTOPICS, at their current values.
TOO_MANY_CHOSEN = "Choose at most {count} topics"
TOO_MANY_SUBTOPICS = "A topic can have at most {count} subtopics"

# A generation stops after this long: Cloud Tasks gives one request at most 30 minutes.
JOB_TIMEOUT_SECONDS = 25 * 60
# How long Cloud Tasks waits for the worker's answer; a little over JOB_TIMEOUT_SECONDS.
TASK_DEADLINE_SECONDS = 28 * 60
# Queueing a job is answered within this, well inside the 15 s companies waits to start one.
ENQUEUE_TIMEOUT_SECONDS = 5
CLOUD_TASKS_URL = "https://cloudtasks.googleapis.com"
# The worker's job endpoints.
RUN_GENERATION = "/internal/jobs/run-generation"
VERIFY_QUESTION = "/internal/jobs/verify-question"
TRANSLATE_NEWS = "/internal/jobs/translate-news"
TRANSLATE_CAMPAIGN = "/internal/jobs/translate-campaign"
# A running job updates its row as it goes; one untouched for longer than a job may run has lost
# its worker. The margin covers the last update coming a little before the timeout.
STUCK_AFTER_SECONDS = JOB_TIMEOUT_SECONDS + 10 * 60
# A queued generation may only be waiting for a free worker; one queued this long has lost its
# job (the queue failed to take it).
QUEUED_STUCK_AFTER_SECONDS = 2 * 60 * 60

GENERATION_FAILED = "Generation failed. Please try again."
GENERATION_STOPPED = "Generation stopped unexpectedly. Please try again."
# Topics left waiting for review this long are cancelled; nothing has been generated yet.
REVIEW_EXPIRY_DAYS = 14

# Extraction and drafted topics are reused for the same prompt and input for this long.
DRAFT_CACHE_SECONDS = 30 * 24 * 60 * 60

# Redis counters for the LLM requests made in each second, shared by all generation processes.
LLM_RATE_KEY = "rate:llm"
# A call held back for the next second waits up to this much longer, at random, so the held calls
# don't all ask again at the same instant (and collide again, each ask a paid Redis command).
LLM_WAIT_JITTER_SECONDS = 0.3
# Connections of the checkpointer's own pool, on top of the SQLAlchemy pool.
CHECKPOINTER_POOL_SIZE = 2

# The daily generation budget: its counter, kept a little over a day, and the refusal.
BUDGET_KEY = "budget:generations"
BUDGET_KEY_SECONDS = 2 * 24 * 60 * 60
GENERATIONS_PAUSED = (
    "We've reached today's limit for new generations. Please try again tomorrow; practice and "
    "interviews keep working."
)
# Notifications asks for at most this many generations' statuses in one call (its reminders).
MAX_STATUSES_PER_CALL = 1000

# A review sent for a generation that isn't waiting for one (already reviewed, or never drafted).
NOT_AWAITING_REVIEW = "Generation is not awaiting review"
