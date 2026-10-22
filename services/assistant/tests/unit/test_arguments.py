from app.helpers.arguments import fill_path, problems, texts_in

PARAMETERS = {
    "type": "object",
    "properties": {
        "interview_id": {"type": "string", "format": "uuid"},
        "q": {"type": "string", "maxLength": 5},
        "status": {"type": "string", "enum": ["finished", "passed"]},
        "limit": {"type": "integer", "minimum": 1, "maximum": 20},
    },
    "required": ["interview_id"],
}
INTERVIEW = "3f2b6a1e-8a7c-4c1e-9a55-0b6f3c2d1e00"


def test_valid_arguments_have_no_problems_and_nulls_are_left_out():
    arguments = {"interview_id": INTERVIEW, "q": "ann", "status": None, "limit": 20}

    assert problems(arguments, PARAMETERS) == []


def test_every_problem_is_named():
    arguments = {
        "q": "too long",
        "status": "hired",
        "limit": True,
        "other": 1,
    }

    assert problems(arguments, PARAMETERS) == [
        "unknown argument other",
        "interview_id is required",
        "q must be at most 5 characters",
        "status must be one of ['finished', 'passed']",
        "limit must be of type integer",
    ]


def test_ids_and_bounds_are_checked():
    assert problems({"interview_id": "../../internal"}, PARAMETERS) == [
        "interview_id must be a UUID"
    ]
    assert problems({"interview_id": INTERVIEW, "limit": 0}, PARAMETERS) == [
        "limit must be at least 1"
    ]
    assert problems({"interview_id": INTERVIEW, "limit": 21}, PARAMETERS) == [
        "limit must be at most 20"
    ]


def test_path_values_are_escaped_as_one_segment():
    assert (
        fill_path("/{provider}/jobs", {"provider": "work able/../x"})
        == "/work%20able%2F..%2Fx/jobs"
    )


def test_an_empty_required_text_is_missing_and_the_model_is_told_to_ask():
    parameters = {
        "type": "object",
        "properties": {"name": {"type": "string"}, "note": {"type": "string"}},
        "required": ["name"],
    }

    assert problems({"name": "  ", "note": ""}, parameters) == [
        "name is empty: ask the user for it"
    ]
    assert problems({"name": "Acme"}, parameters) == []


def test_every_string_in_the_arguments_is_found_however_deep():
    arguments = {"a": "one", "b": [1, "two", {"c": ["three"]}], "d": None, "e": True}

    assert sorted(texts_in(arguments)) == sorted(["a", "one", "b", "two", "c", "three", "d", "e"])
