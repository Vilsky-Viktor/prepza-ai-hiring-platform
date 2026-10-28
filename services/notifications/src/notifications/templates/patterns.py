# How the layout puts an email's pieces together, with each language's punctuation: the plain
# text's heading as a sentence, a label before its link ({value} may be empty), and a second note
# after the footer. A language not listed writes them as English does.
PATTERNS = {
    "en": {
        "sentence": "{text}.",
        "labelled": "{label}: {value}",
        "joined": "{first} {second}",
    },
    # A no-break space before the colon, as the French texts write it.
    "fr": {
        "sentence": "{text}.",
        "labelled": "{label} : {value}",
        "joined": "{first} {second}",
    },
    # The danda ends a Hindi sentence.
    "hi": {
        "sentence": "{text}।",
        "labelled": "{label}: {value}",
        "joined": "{first} {second}",
    },
    # Full-width marks, and no space between sentences.
    "ja": {
        "sentence": "{text}。",
        "labelled": "{label}：{value}",
        "joined": "{first}{second}",
    },
    "zh": {
        "sentence": "{text}。",
        "labelled": "{label}：{value}",
        "joined": "{first}{second}",
    },
    # Thai ends a sentence with no mark; a space sets sentences apart.
    "th": {
        "sentence": "{text}",
        "labelled": "{label}: {value}",
        "joined": "{first} {second}",
    },
}
