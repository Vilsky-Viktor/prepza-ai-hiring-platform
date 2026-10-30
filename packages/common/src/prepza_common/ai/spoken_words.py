"""How far spoken words are from the text that was to be said: rounds' check of a question read
aloud (the speech model's own transcript against the script) and the evals' reading test. Word by
word, case and punctuation aside."""

import re
import unicodedata


def words(text: str) -> list[str]:
    """The text's words, case and punctuation aside; a hyphen or a slash splits them ("B-tree"
    and "B tree" alike)."""
    text = unicodedata.normalize("NFKC", text).lower()

    return re.findall(r"[^\W_]+", text)


def word_errors(said: str, heard: str) -> tuple[float, int]:
    """The word error rate of what was heard against what was said (words substituted, left out
    or added, over the words said), and the longest run of words added in one place (an answer
    or a comment the speaker put in)."""
    a, b = words(said), words(heard)
    # Each cell: (edits, longest added run so far, the added run ending here).
    row = [(j, j, j) for j in range(len(b) + 1)]

    for i, x in enumerate(a, 1):
        previous, row[0] = row[0], (i, 0, 0)

        for j, y in enumerate(b, 1):
            dropped = (row[j][0] + 1, row[j][1], 0)
            run = row[j - 1][2] + 1
            added = (row[j - 1][0] + 1, max(row[j - 1][1], run), run)
            kept = (previous[0] + (x != y), previous[1], 0)
            previous, row[j] = row[j], min(kept, dropped, added, key=lambda cell: cell[0])

    edits, longest, _ = row[-1]

    return edits / max(len(a), 1), longest
