# Tools the panel itself carries out, in the browser: the model only tells it to.
SIGN_OUT = "sign_out"
SIGN_OUT_DEFINITION = {
    "type": "function",
    "function": {
        "name": SIGN_OUT,
        "description": (
            "Sign the user out of prepza at once (the panel does it). Use it only when they ask "
            "to sign out or log out."
        ),
        "parameters": {
            "type": "object",
            "properties": {},
            "required": [],
            "additionalProperties": False,
        },
    },
}
SIGN_OUT_FOR_MODEL = "The panel is signing the user out now; say goodbye in one short sentence."
