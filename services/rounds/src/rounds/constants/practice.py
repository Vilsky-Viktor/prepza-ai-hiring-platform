# Free practice rounds on a template: questions per topic in a round (picked at random from its
# revealed questions). Each has the seconds a company's new test of its level starts with
# (testee_common.limits.limits.question_seconds).
PRACTICE_TOPIC_QUESTIONS = 10
NO_PRACTICE_QUESTIONS = "This interview has no practice questions yet."
# How long the public question count of a template's round is kept before it's asked again.
PRACTICE_SIZE_CACHE_SECONDS = 5 * 60
# The time per question a talent chooses before a round (WCAG 2.2.1, timing adjustable): practice
# measures nothing, so it offers more time or none. Each is a multiple of the level's seconds;
# None means untimed.
PRACTICE_TIMINGS: dict[str, int | None] = {"standard": 1, "double": 2, "untimed": None}
STANDARD_TIMING = "standard"
