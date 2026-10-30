# A spoken yes, by voice mode's languages: a reply made only of these (each part on its own, as
# speech recognition writes them: lower case, punctuation between parts) confirms the choice
# waiting, without a matching call (helpers/voice_match.py obvious). Only words that mean yes
# and nothing else as a reply to "Is that your answer?"; anything else goes to the model.
CONFIRMATIONS: dict[str, frozenset[str]] = {
    "en": frozenset(
        {
            "yes",
            "yeah",
            "yep",
            "yup",
            "sure",
            "correct",
            "right",
            "exactly",
            "that's right",
            "that's correct",
            "that's it",
        }
    ),
    "es": frozenset({"sí", "si", "correcto", "exacto", "eso es", "así es", "claro"}),
    "de": frozenset({"ja", "genau", "richtig", "korrekt", "stimmt", "passt", "jawohl", "jep"}),
    "fr": frozenset(
        {"oui", "exact", "exactement", "c'est ça", "c'est correct", "tout à fait", "ouais"}
    ),
    "pt": frozenset({"sim", "correto", "certo", "isso", "isso mesmo", "exato", "é isso"}),
    "it": frozenset({"sì", "si", "esatto", "corretto", "giusto", "certo", "proprio così"}),
}
