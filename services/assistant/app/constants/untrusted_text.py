# What the assistant drops from data before it fills an action's text
# (helpers/untrusted_text.py): content a reader doesn't see, and parts addressed to an AI.
# English cues only; hidden content is found in any language.
import re

# Hidden in HTML: comments (also one left open), scripts and styles, and elements styled or
# marked hidden; then any other tag, whose visible words stay.
COMMENT = re.compile(r"<!--.*?(?:-->|\Z)", re.DOTALL)
HIDDEN_BLOCK = re.compile(
    r"<(script|style|template)\b[^>]*>.*?(?:</\1\s*>|\Z)", re.DOTALL | re.IGNORECASE
)
HIDDEN_ELEMENT = re.compile(
    r"<([a-z][a-z0-9]*)\b[^>]*?(?:\shidden\b|aria-hidden\s*=\s*[\"']?true"
    r"|display\s*:\s*none|visibility\s*:\s*hidden|opacity\s*:\s*0(?:\.0+)?\s*(?:[;\"']|$)"
    r"|font-size\s*:\s*0(?:\.0+)?(?:px|pt|em|rem|%)?\s*(?:[;\"']|$))[^>]*>.*?(?:</\1\s*>|\Z)",
    re.DOTALL | re.IGNORECASE,
)
TAG = re.compile(r"</?[a-z][a-z0-9-]*(?:\s[^<>]*)?/?>", re.IGNORECASE)
# Characters that show nothing: zero-width space, word joiner and invisible operators, the byte
# order mark, direction overrides and isolates, and Unicode tag characters. Zero-width
# (non-)joiners stay: Persian, Hindi and emoji need them.
INVISIBLE = re.compile(
    "[\u180e\u200b\u202a-\u202e\u2060-\u2064\u2066-\u2069\ufeff\U000e0000-\U000e007f]"
)

# Parts: sentences (an end mark before a space or a capital, or a line's end), and asides in
# brackets (one level of brackets inside them).
SENTENCE_END = re.compile(r"(?<=[.!?])(?=\s|[A-Z])|(?<=\n)")
BRACKETED = re.compile(r"\s*[\[(](?:[^\[\]()]|[\[(][^\[\]()]*[\])])*[\])]")

AI = r"(?:AI|assistant|AI assistant|AI agent|chatbot|bot|LLM|GPT|language model|copilot|system)"
# A part that starts by addressing an AI ("Assistant, …", "SYSTEM: …") and tells it to act.
ADDRESSED = re.compile(
    rf"^\W*(?:(?:hey|hi|dear|attention|to)\s+)?(?:the\s+)?{AI}\s*[:,]", re.IGNORECASE
)
ACTS = re.compile(
    r"\b(?:ignore|disregard|forget|delete|remove|invite|rename|revoke|disconnect|grant|approve"
    r"|transfer|forward|call|also)\b",
    re.IGNORECASE,
)
# A part that is an instruction to an AI wherever it starts.
INSTRUCTIONS = (
    re.compile(
        rf"\b(?:note|message|instructions?|command|request|prompt|memo)s?\s+(?:to|for)\s+"
        rf"(?:the\s+|any\s+|an\s+|all\s+)?{AI}s?\b(?!\s+(?:team|department|group|lab|product))",
        re.IGNORECASE,
    ),
    re.compile(
        rf"\b{AI}s?\s+(?:reading|processing|parsing|seeing|reviewing)\s+this\b", re.IGNORECASE
    ),
    re.compile(
        r"\b(?:ignore|disregard|forget|override)\s+(?:all\s+|any\s+|the\s+|your\s+|of\s+)*"
        r"(?:previous|prior|above|earlier|preceding|former|original|system|these)\s+"
        r"(?:instructions|rules|prompts?|directions|guidelines)\b",
        re.IGNORECASE,
    ),
    re.compile(r"\byou\s+are\s+now\s+(?:in\s+)?(?:an?\s+)?[\w-]+\s+mode\b", re.IGNORECASE),
    re.compile(
        r"\b(?:do\s+not|don't|never)\s+(?:mention|tell|reveal)\s+(?:this|it|the\s+user)\b",
        re.IGNORECASE,
    ),
)
