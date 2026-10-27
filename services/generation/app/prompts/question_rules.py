# Rules every prompt that writes questions or their options shares (questions.py, answers.py,
# regenerate.py), so a question reads the same however it was made. Plain text without braces:
# the prompts that include them are filled with str.format.

# Who writes questions and their options, for every prompt that does (rule 19: a role
# generic to prepza's work, never one job, field or language).
QUESTION_WRITER_ROLE = (
    "You are an assessment designer who writes multiple-choice questions for the skills "
    "tests companies give job candidates, in any field."
)

# The whole question, its example and its four options read and answered within a minute (a
# minute and a half for the hardest), also by someone reading in a language that isn't their own
# (constants/generation.py checks the limits).
READING_RULES = """Length: a capable candidate at the given level reads the question, its example and
all four options and answers within one minute, often in a language that isn't their own. Only
the hardest questions (hard level, several steps of reasoning, or select-all-that-apply) may take
up to a minute and a half, never more.
- The question is at most 40 words (a hard one at most 50): one or two short sentences that
  give only what the answer depends on. No story, no names of people or companies, no
  background that doesn't change the answer.
- Plain, common words and simple sentence structure; one idea per sentence. The topic's own
  terms are fine; rare words, idioms and wordplay are not.
- An example is at most 8 short lines, and only as long as the question needs: the lines the
  answer depends on, with no setup or boilerplate that doesn't change it, short names, and the
  fewest records, values or details that still make the case. It shows one piece, such as one
  file, unless the question is about how several pieces work together.
- A scenario or a worked example states every detail the answer depends on, so that only one
  answer holds, and nothing else, in as few words as that takes.
- Each option is at most 10 words.
A question is hard because of the reasoning it needs, never because of its length."""

LEVEL_GUIDE = """How hard the questions are, by level:
- basic: core ideas and terms, and applying them in simple, typical cases.
- medium: using the knowledge in realistic situations: choosing between options, predicting
  what happens, spotting a mistake, working out a result.
- hard: what a senior person is tested on: trade-offs, edge cases, diagnosing a problem from
  its symptoms, multi-step reasoning and decisions under constraints. Few questions are plain
  recall of a definition or a fact; most give a short situation or example and ask about it.
  Hard comes from the thinking the question needs, never from its length.
  A scenario alone doesn't make a question hard: if one known rule, fact or single calculation
  answers it, it is medium. A hard question needs two or more steps, or weighing factors that
  pull in different directions, and its wrong options are what a capable mid-level person
  would pick.
Most questions are at the given level; a few are one level easier or harder."""

PRACTICE_GUIDE = """Make them practice, not trivia. Mix these kinds, as the subtopic allows:
- A short scenario with the few concrete details that matter, asking what to do, choose or
  expect.
- A worked example with real numbers, asking for the result or the best estimate.
- When the subtopic itself is about writing or reading a formal notation that a computer runs or
  reads exactly as written (instructions, lookups over stored records, commands, settings
  files, text-matching patterns), about a third of the questions (how many is given above) come
  with a short, concrete example in it and ask what it produces, what it does, why it fails, or
  which change fixes it. This holds even when the subtopic sounds conceptual: show a real
  example of it. When the example acts on stored records, it first lists the few records
  involved, then the instructions. The options are then exact results on one line each: the
  values produced, the records returned, or the name of the error. Keep each example small
  enough that its result is certain: nothing that depends on timing, the order of concurrent
  work, random values, memory addresses, today's date or the version in use.
- Any other subtopic may show a short artefact as its example where the subtopic naturally works
  with one, such as a few rows of data, figures, a schedule or a record, in at most about a
  third of the questions; never a notation a computer runs that the field itself doesn't use.
  A language people speak is not a formal notation: a sentence to read or translate stays in
  the question itself, in quotation marks, and has no example.
- Only some questions ask what a term means or which statement is true."""

DISTRACTOR_RULES = """- Each distractor is a specific, believable mistake: a common misconception, a confusion
  with a related idea, steps in the wrong order, a typical miscalculation, or the result of a
  wrong assumption. Someone who half-knows the topic should find it tempting.
- Distractors are clearly wrong to someone who knows the topic.
- All options have the same form: the same grammatical structure, the same kind of thing (all
  numbers, all actions, all tools) and a similar level of detail.
- The correct options must not stand out. Write each in as few words as it needs, then write
  each distractor with about the same number of words, never noticeably fewer: across a set of
  questions a correct option is the longest of the four no more often than any other.
- An option is a single line of at most 10 words; several printed values go on that line,
  separated by spaces.
- No "all of the above", "none of the above", or options that overlap with a correct one.
- A distractor must be wrong for the question exactly as written, not merely less precise. If
  an expert could defend it as a correct answer, it is not a distractor."""

# The two kinds of question (prepza_common.ai.multi_answer): the candidate picks one option, or ticks
# every correct one of a select-all-that-apply question, which scores only when no wrong one is
# ticked. Each prompt that writes questions or options says which kind it wants.
SINGLE_ANSWER_RULES = """- A single-answer question has exactly one clearly correct option that can be stated
  concisely. Avoid questions that several answers could fit, such as asking for "a" tool,
  term, or step when several take part. Ask for the one that is specifically right."""

MULTI_ANSWER_RULES = """- A select-all-that-apply question asks which of the options are true, apply, or fit the
  situation: 2 or 3 of its 4 options are correct, never all of them; write as many with 3
  correct as with 2. The screen tells the candidate to select all that apply, so the
  question doesn't say it. Never ask for the best, first or main one: that has one answer.
- Each option is judged on its own, so every one must be clearly correct or clearly wrong under
  the conditions the question states, and experts would mark each one the same way:
  - The question states every condition an option's truth depends on: the standard, framework,
    law, version or convention in use, for a language people speak its region and register,
    and the values and the case it is about. Never leave a case open that would flip an option
    ("if the two are equal", "in some countries", "depending on the tool").
  - A correct option is correct by itself, not only together with another option, and it does
    what the question asks, not a neighbouring goal: a step that serves another purpose is wrong
    even when it is good practice.
  - A wrong option is wrong in every case the question allows, not merely weaker or less usual.
  - No "usually", "often", "can", "may" or "might" in options when that makes them true or false
    depending on how they are read.
- The wrong options are what makes the question hard: each is a mistake someone who half-knows
  the topic would tick. Build each from one of these:
  - a well-known rule applied one step too far, to a case where it no longer holds;
  - a statement that is true in a closely related case (another version, standard, setting or
    order of steps) but not in the one stated;
  - a correct statement with one detail changed: a number, a direction, a cause and its effect
    swapped, or "always" where it is "only when";
  - a widespread belief in the field that is false.
  Never an obviously absurd, off-topic or joking option. With 3 correct, the one wrong option
  is the hardest to spot: it reads like the three right ones and holds in a closely related
  case.
- Right and wrong options read alike: the same length, tone and level of detail, equally
  confident and precise, so neither the textbook-sounding wording nor the hedging gives the
  key away. At least one right option is less obvious: a consequence or an exception a
  half-knowing person would doubt, yet one that holds without exception under the stated
  conditions.
- Before writing a select-all-that-apply question down, check each option against the question
  as written; if any one could be argued either way, change the question or the option, or
  write a different question."""
