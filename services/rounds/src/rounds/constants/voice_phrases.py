# What the interviewer says besides the question and its options, read aloud in the interview's
# language and cached once per language (helpers/voice_speech.py); translated by their English
# text, as error messages are.
from enum import StrEnum

# In place of a code block or a long example, which isn't read aloud.
LOOK_AT_EXAMPLE = "Look at the example on screen."
# A select-all-that-apply question, after its text.
CHOOSE_ALL = "Pick multiple options for this question."
# Each option as it's read: its letter, then its text.
OPTION = "{letter}: {text}."
# An option with code or a long example in it, instead of its text.
OPTION_ON_SCREEN = "{letter}: shown on screen."
# The last two letters of a choice of several: "A, C and D".
LAST_TWO = "{first} and {last}"
CONFIRM = "You chose {letters}. Is that right?"
# A clear answer (one option on a single-answer question), saved without asking to confirm it.
SAVED = "{letter}, saved."
UNCLEAR = "Sorry, I didn't catch that. Say your answer again, or tap an option."
AGAIN = "All right. Which option do you choose?"
# At once when the candidate stops speaking, while their answer is understood.
GOT_IT = "Got it."
# Before the next question: after a confirmed answer, or when the question's time ran out.
NEXT = "Moving on to the next question."
TIME_UP = "Time's up. No answer. Moving on to the next question."
# When the question's time ran out with an answer picked, which was saved.
TIME_UP_SAVED = "Time's up. Your answer is saved. Moving on to the next question."
END = "Thank you. Your answers are recorded, and the company will be in touch about the results."


class Phrase(StrEnum):
    """The interviewer's fixed phrases the browser asks for by name."""

    UNCLEAR = "unclear"
    AGAIN = "again"
    GOT_IT = "got-it"
    NEXT = "next"
    TIME_UP = "time-up"
    TIME_UP_SAVED = "time-up-saved"
    END = "end"


FIXED_PHRASES = {
    Phrase.UNCLEAR: UNCLEAR,
    Phrase.AGAIN: AGAIN,
    Phrase.GOT_IT: GOT_IT,
    Phrase.NEXT: NEXT,
    Phrase.TIME_UP: TIME_UP,
    Phrase.TIME_UP_SAVED: TIME_UP_SAVED,
    Phrase.END: END,
}
