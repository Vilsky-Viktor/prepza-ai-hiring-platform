# What the assistant drops from data before it fills an action's text
# (helpers/untrusted_text.py): content a reader doesn't see, and parts addressed to an AI.
# Hidden content is found in any language. Parts addressed to an AI are found by English cues,
# and in every interface language by "ignore the previous instructions" alone: a vocative or
# "note to the assistant" in other languages depends on their grammar and, in Chinese, Japanese
# and Thai, on words without spaces between them, so matching it would cut real job text.
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
# Chinese and Japanese end marks need no space after them; Arabic, Persian and Hindi have
# their own.
SENTENCE_END = re.compile(r"(?<=[.!?\u061f\u0964])(?=\s|[A-Z])|(?<=[\u3002\uff01\uff1f])|(?<=\n)")
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
    # "Ignore (all) the previous instructions" in the other interface languages.
    re.compile(
        r"ignorier\w*\s+(?:alle\s+)?(?:\w+\s+)?(?:vorherigen|bisherigen|obigen)\s+anweisungen"
        r"|ignora\w*\s+(?:todas\s+|tutte\s+)?(?:las|le)\s+(?:instrucciones|istruzioni)\s+"
        r"(?:anteriores|precedenti)"
        r"|ignore[rz]?\s+(?:toutes\s+)?les\s+instructions\s+pr\u00e9c\u00e9dentes"
        r"|ignor[ae]r?\s+(?:todas\s+)?as\s+instru\u00e7\u00f5es\s+anteriores"
        r"|negeer\s+(?:alle\s+)?(?:eerdere|vorige)\s+instructies"
        r"|zignoruj\s+(?:wszystkie\s+)?(?:poprzednie|wcze\u015bniejsze)\s+instrukcje"
        r"|(?:игнорируй|забудь)\s+(?:все\s+)?(?:предыдущие|прежние)\s+инструкции"
        r"|(?:ігноруй|забудь)\s+(?:усі\s+|всі\s+)?попередні\s+інструкції"
        r"|önceki\s+(?:tüm\s+)?talimatları\s+(?:yok\s+say|görmezden\s+gel)"
        r"|abaikan\s+(?:semua\s+)?instruksi\s+sebelumnya"
        r"|bỏ\s+qua\s+(?:tất\s+cả\s+)?(?:các\s+)?hướng\s+dẫn\s+trước"
        r"|(?:huwag\s+pansinin|balewalain)\s+(?:ang\s+)?(?:lahat\s+ng\s+)?"
        r"(?:naunang|nakaraang)\s+(?:mga\s+)?(?:tagubilin|instruksyon)"
        r"|ignoreeri\s+(?:kõiki\s+)?(?:eelmisi|varasemaid)\s+juhiseid"
        r"|تجاهل\s+(?:جميع\s+|كل\s+)?التعليمات\s+السابقة"
        r"|(?:دستورالعمل|دستور)\S*\s+قبلی\s+را\s+نادیده\s+بگیر"
        r"|התעלם\s+מ(?:כל\s+)?ה?הוראות\s+ה?קודמות"
        r"|पिछले\s+(?:सभी\s+)?निर्देशों\s+को\s+(?:अनदेखा|नज़रअंदाज़|नजरअंदाज)"
        r"|(?:以前|前|上記)の(?:すべての)?指示を無視"
        r"|이전\s*(?:의\s*)?(?:모든\s*)?(?:지시|지침)\S*\s*무시"
        r"|忽略(?:之前|以前|先前|上面)(?:的)?(?:所有)?(?:指令|指示)"
        r"|(?:เพิกเฉย|ละเว้น)(?:ต่อ)?คำสั่ง(?:ทั้งหมด)?ก่อนหน้า",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:do\s+not|don't|never)\s+(?:mention|tell|reveal)\s+(?:this|it|the\s+user)\b",
        re.IGNORECASE,
    ),
)
