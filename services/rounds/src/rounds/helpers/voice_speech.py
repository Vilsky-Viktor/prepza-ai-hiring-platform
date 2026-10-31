import hashlib
import io
import re
import struct

import av
from testee_common.ai.spoken_words import word_errors
from testee_common.i18n.i18n import translate

from rounds.constants.voice import (
    LETTERS,
    MAX_ADDED_WORDS,
    MAX_READING_WORD_ERRORS,
    MAX_SPOKEN_CHARACTERS,
    OPUS_BIT_RATE,
    SPEECH_RATE,
)
from rounds.constants.voice_phrases import (
    CHOOSE_ALL,
    CONFIRM,
    LAST_TWO,
    LOOK_AT_EXAMPLE,
    OPTION,
    OPTION_ON_SCREEN,
    SAVED,
)
from rounds.schemas.rounds import NextQuestion

# A fenced code block, as the frontend shows one (lib/question-text.ts).
CODE_BLOCK = re.compile(r"```[\s\S]*?```")
INLINE_CODE = re.compile(r"`([^`\n]+)`")
# An option this long, or on several lines, is an example to read on screen.
MAX_SPOKEN_OPTION = 160
# Opus always counts its samples at 48 kHz, whatever it was recorded at.
OPUS_RATE = 48_000


def spoken_text(text: str) -> tuple[str, bool]:
    """A question's text as it's read: inline code read as words, and whether a code block was
    left out."""
    has_code = bool(CODE_BLOCK.search(text))
    prose = INLINE_CODE.sub(r"\1", CODE_BLOCK.sub(" ", text))

    return " ".join(prose.split()), has_code


def read_aloud(option: str) -> bool:
    """Whether an option is read as it is: not code, a long example or several lines."""
    return "`" not in option and "\n" not in option and len(option) <= MAX_SPOKEN_OPTION


def question_script(question: NextQuestion, language: str) -> str:
    """What the interviewer reads for a question: its text (a code block replaced by a pointer to
    the screen), a select-all-that-apply note, then each option with its letter; an option with
    code or a long example is said to be on screen. Cut to MAX_SPOKEN_CHARACTERS."""
    prose, has_code = spoken_text(question.text)
    parts = [prose]

    if has_code:
        parts.append(translate(LOOK_AT_EXAMPLE, language))

    if question.multi:
        parts.append(translate(CHOOSE_ALL, language))

    for letter, option in zip(LETTERS, question.options, strict=False):
        if read_aloud(option):
            parts.append(translate(OPTION, language).format(letter=letter, text=option.strip()))
        else:
            parts.append(translate(OPTION_ON_SCREEN, language).format(letter=letter))

    return " ".join(parts)[:MAX_SPOKEN_CHARACTERS]


def letters_said(picks: list[int], language: str) -> str:
    """Options' letters as said: "B", or "A, C and D"."""
    letters = [LETTERS[pick] for pick in sorted(picks)]

    if len(letters) == 1:
        return letters[0]

    last_two = translate(LAST_TWO, language).format(first=letters[-2], last=letters[-1])

    return ", ".join([*letters[:-2], last_two])


def confirmation(picks: list[int], language: str) -> str:
    return translate(CONFIRM, language).format(letters=letters_said(picks, language))


def saved_answer(pick: int, language: str) -> str:
    return translate(SAVED, language).format(letter=LETTERS[pick])


def clip_key(model: str, voice: str, language: str, text: str) -> str:
    """One clip per text read in one voice: the same question in two interviews is read once."""
    return hashlib.sha256(f"{model}\n{voice}\n{language}\n{text}".encode()).hexdigest()


def ogg_seconds(audio: bytes) -> float:
    """How long an Ogg Opus clip plays: its last page's sample position, less the encoder's
    pre-skip, at 48 kHz; 0 for anything else."""
    last = audio.rfind(b"OggS")
    head = audio.find(b"OpusHead")

    if last < 0 or head < 0 or len(audio) < last + 14 or len(audio) < head + 12:
        return 0.0

    (position,) = struct.unpack_from("<q", audio, last + 6)
    (pre_skip,) = struct.unpack_from("<H", audio, head + 10)

    return max(0.0, (position - pre_skip) / OPUS_RATE)


def pcm_seconds(pcm: bytes) -> float:
    """How long the speech model's audio (16-bit mono PCM at SPEECH_RATE) plays."""
    return len(pcm) / 2 / SPEECH_RATE


def ogg_opus(pcm: bytes) -> bytes:
    """The speech model's audio as Ogg Opus, as clips are kept and played."""
    out = io.BytesIO()

    with av.open(out, "w", format="ogg") as container:
        stream = container.add_stream("libopus", rate=SPEECH_RATE, layout="mono")
        stream.bit_rate = OPUS_BIT_RATE
        frame = av.AudioFrame(format="s16", layout="mono", samples=len(pcm) // 2)
        frame.sample_rate = SPEECH_RATE
        frame.planes[0].update(pcm)
        container.mux(stream.encode(frame))
        container.mux(stream.encode(None))

    return out.getvalue()


def strays(text: str, transcript: str) -> bool:
    """The reading, by the model's own transcript, isn't the text: too many words wrong, or words
    added in one place (an answer, a comment)."""
    rate, added = word_errors(text, transcript)

    return rate > MAX_READING_WORD_ERRORS or added >= MAX_ADDED_WORDS
