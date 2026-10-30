# What the interviewer says besides the question and its options, read aloud in the interview's
# language and cached once per language (helpers/voice_speech.py); translated by their English
# text, as error messages are.
from enum import StrEnum

# In place of a code block or a long example, which isn't read aloud.
LOOK_AT_EXAMPLE = "Look at the example on screen."
# A select-all-that-apply question, after its text.
CHOOSE_ALL = "Choose every option that applies."
# Each option as it's read: its letter, then its text.
OPTION = "{letter}: {text}."
# An option with code or a long example in it, instead of its text.
OPTION_ON_SCREEN = "{letter}: shown on screen."
# The last two letters of a choice of several: "A, C and D".
LAST_TWO = "{first} and {last}"
CONFIRM = "You chose {letters}. Is that right?"
UNCLEAR = "Sorry, I didn't catch that. Say the letter of your answer, or tap an option."
REMINDER = "Take your time. Say the letter of your answer when you're ready."
AGAIN = "All right. Which option do you choose?"
END = "Thank you. Your answers are recorded, and the company will be in touch about the results."


class Phrase(StrEnum):
    """The interviewer's fixed phrases the browser asks for by name."""

    UNCLEAR = "unclear"
    REMINDER = "reminder"
    AGAIN = "again"
    END = "end"


FIXED_PHRASES = {
    Phrase.UNCLEAR: UNCLEAR,
    Phrase.REMINDER: REMINDER,
    Phrase.AGAIN: AGAIN,
    Phrase.END: END,
}
