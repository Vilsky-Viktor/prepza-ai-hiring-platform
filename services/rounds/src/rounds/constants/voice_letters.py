# Option letters said plainly, by voice mode's languages: a reply made only of letters, each
# alone or after one of these words ("option B", "la respuesta C"), joined by commas or one of
# these words for "and" ("B and D"), is read by code without the matching call
# (helpers/voice_letters.py). Only words that can't change which option is meant; anything else
# ("not A", "B or C") goes to the model. Lower case, as the reply is compared.
LETTER_WORDS: dict[str, frozenset[str]] = {
    "en": frozenset({"option", "answer", "letter"}),
    "es": frozenset(
        {"la", "opción", "la opción", "respuesta", "la respuesta", "letra", "la letra"}
    ),
    "de": frozenset({"option", "antwort", "buchstabe"}),
    "fr": frozenset({"la", "option", "l'option", "réponse", "la réponse", "lettre", "la lettre"}),
    "pt": frozenset(
        {
            "opção",
            "a opção",
            "resposta",
            "a resposta",
            "letra",
            "a letra",
            "alternativa",
            "a alternativa",
        }
    ),
    "it": frozenset(
        {"la", "opzione", "l'opzione", "risposta", "la risposta", "lettera", "la lettera"}
    ),
}
AND_WORDS: dict[str, frozenset[str]] = {
    "en": frozenset({"and"}),
    "es": frozenset({"y", "e"}),
    "de": frozenset({"und"}),
    "fr": frozenset({"et"}),
    "pt": frozenset({"e"}),
    "it": frozenset({"e", "ed"}),
}
