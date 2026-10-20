import re

# Words that name a technology, a standard or a field: prompts must work for any domain.
FIELD_TERMS = (
    "debug",
    "software",
    "engineer",
    "code",
    "technical",
    "technology",
    "program",
    "sql",
    "query",
    "shell",
    "spreadsheet",
    "regular expression",
    "regex",
    "python",
    "javascript",
    "typescript",
    "rust",
    "decorator",
    "transaction",
    "database",
    "ifrs",
    "gaap",
    "crm",
    "salesforce",
    "hubspot",
    "seo",
    "marketing",
    "accounting",
    "nursing",
    "keyword",
)


def test_generation_prompts_name_no_technology_standard_or_field():
    from app.prompts.question_rules import QUESTION_WRITER_ROLE
    from app.prompts.answers import ANSWERS_REQUEST, ANSWERS_SYSTEM, MULTI_ANSWER_KIND
    from app.prompts.code_languages import CODE_LANGUAGES_PROMPT
    from app.prompts.extraction import EXTRACTION_SYSTEM, TEMPLATE_TITLE_RULE
    from app.prompts.questions import QUESTIONS_REQUEST, QUESTIONS_SYSTEM
    from app.prompts.regenerate import (
        REGENERATE_REQUEST,
        REGENERATE_SYSTEM,
        REPORT_GUIDANCE,
        REPORTS,
    )
    from app.prompts.topics import REVISION_PROMPT, TOPICS_PROMPT
    from app.prompts.verify import CONFIRM_PROMPT, SELF_CHECK_PROMPT, VERIFY_PROMPT
    from app.schemas.questions import EXAMPLE, EXAMPLE_LANGUAGE

    prompts = [
        QUESTION_WRITER_ROLE,
        ANSWERS_SYSTEM,
        ANSWERS_REQUEST,
        MULTI_ANSWER_KIND,
        CODE_LANGUAGES_PROMPT,
        EXTRACTION_SYSTEM,
        TEMPLATE_TITLE_RULE,
        QUESTIONS_SYSTEM,
        QUESTIONS_REQUEST,
        REGENERATE_SYSTEM,
        REGENERATE_REQUEST,
        REPORTS,
        *REPORT_GUIDANCE.values(),
        TOPICS_PROMPT,
        REVISION_PROMPT,
        VERIFY_PROMPT,
        CONFIRM_PROMPT,
        SELF_CHECK_PROMPT,
        EXAMPLE,
        EXAMPLE_LANGUAGE,
    ]

    for prompt in prompts:
        for term in FIELD_TERMS:
            assert not re.search(rf"\b{term}", prompt.lower()), term

    # Every prompt that writes questions or options starts with the same generic role (rule 19),
    # in its system message; the per-call request has none.
    for system in (QUESTIONS_SYSTEM, ANSWERS_SYSTEM, REGENERATE_SYSTEM):
        assert system.startswith(QUESTION_WRITER_ROLE)
        assert QUESTION_WRITER_ROLE.lower().startswith("you are")

    for request in (QUESTIONS_REQUEST, ANSWERS_REQUEST, REGENERATE_REQUEST):
        assert "you are" not in request.lower()

    assert "multiple-choice" in QUESTIONS_SYSTEM
    assert "multiple-choice" in REGENERATE_SYSTEM
    assert "3-5 sentences" not in ANSWERS_SYSTEM


def test_question_instructions_change_with_no_call_so_the_provider_caches_them():
    from app.services.nodes.questions import question_messages

    task = {"level": "hard", "topic": "T", "subtopic": "S", "count": 9, "multi": 1, "examples": 3}
    first = question_messages({**task, "existing": ["Q1"], "language": "de"})
    second = question_messages({**task, "subtopic": "Other", "count": 5, "language": "ja"})

    assert first[0].type == "system" and first[1].type == "human"
    assert first[0].content == second[0].content
    assert "{" not in first[0].content
    # The topic's own questions are tagged as data in the request, never in the instructions.
    assert "<existing_questions>\n- Q1\n</existing_questions>" in first[1].content
    assert "Q1" not in first[0].content
    assert "German" in first[1].content and "Japanese" in second[1].content


def test_about_a_third_of_the_questions_on_formal_material_come_with_a_short_example():
    from app.prompts.question_rules import PRACTICE_GUIDE, READING_RULES
    from app.prompts.questions import QUESTIONS_REQUEST

    prompt = QUESTIONS_REQUEST.format(
        level="hard",
        topic="T",
        subtopic="S",
        focus="F",
        count=9,
        multi=1,
        examples=3,
        existing="None",
        language="English",
    )

    assert "about a third" in PRACTICE_GUIDE and "at least a third" not in PRACTICE_GUIDE
    assert "exactly 3 of the 9 come with an example" in " ".join(prompt.split())
    # One minute to read and answer; a minute and a half only for the hardest.
    assert "within one minute" in READING_RULES
    assert "up to a minute and a half, never more" in " ".join(READING_RULES.split())
    assert "never because of its length" in READING_RULES
