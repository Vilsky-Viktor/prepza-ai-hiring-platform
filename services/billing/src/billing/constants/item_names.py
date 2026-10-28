# The name of a top-up's item in Paddle's checkout and on its invoice, in the buyer's language:
# for each language, a form for each of its CLDR plural categories, with `{count}` for the
# number as that language writes it. The words are the site's (frontend/messages, the
# `billing.candidates` plural); a category a language lacks falls back to `other`.
CANDIDATES_NAMES = {
    "en": {"one": "{count} candidate", "other": "{count} candidates"},
    "ru": {
        "one": "{count} кандидат",
        "few": "{count} кандидата",
        "many": "{count} кандидатов",
        "other": "{count} кандидата",
    },
    "uk": {
        "one": "{count} кандидат",
        "few": "{count} кандидати",
        "many": "{count} кандидатів",
        "other": "{count} кандидата",
    },
    "es": {"one": "{count} candidato", "other": "{count} candidatos"},
    "pt": {"one": "{count} candidato", "other": "{count} candidatos"},
    "de": {"one": "{count} Kandidat", "other": "{count} Kandidaten"},
    "fr": {"one": "{count} candidat", "other": "{count} candidats"},
    "it": {"one": "{count} candidato", "other": "{count} candidati"},
    "pl": {
        "one": "{count} kandydat",
        "few": "{count} kandydaci",
        "many": "{count} kandydatów",
        "other": "{count} kandydata",
    },
    "nl": {"one": "{count} kandidaat", "other": "{count} kandidaten"},
    "tr": {"other": "{count} aday"},
    "ar": {
        "zero": "لا مرشحين",
        "one": "مرشح واحد",
        "two": "مرشحان",
        "few": "{count} مرشحين",
        "many": "{count} مرشحًا",
        "other": "{count} مرشح",
    },
    "he": {"one": "מועמד אחד", "two": "{count} מועמדים", "other": "{count} מועמדים"},
    "fa": {"other": "{count} متقاضی"},
    "ja": {"other": "候補者 {count} 人"},
    "zh": {"other": "{count} 位候选人"},
    "ko": {"other": "지원자 {count}명"},
    "hi": {"other": "{count} उम्मीदवार"},
    "id": {"other": "{count} kandidat"},
    "th": {"other": "ผู้สมัคร {count} คน"},
    "vi": {"other": "{count} ứng viên"},
    "fil": {"other": "{count} aplikante"},
    "et": {"one": "{count} kandidaat", "other": "{count} kandidaati"},
}
