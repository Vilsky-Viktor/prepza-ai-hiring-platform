"""The comment a candidate's results leave in the ATS that sent them."""

from ats.helpers.ats import result_comment


def test_the_results_comment_says_the_grade_the_outcome_where_the_scorecard_is_and_who_decides():
    text = result_comment("Accountant", 82, True, True, "https://testee.ai/s/1", "en")

    assert text.splitlines() == [
        "testee: Accountant",
        "Grade: 82% (passed)",
        "Integrity signals: yes, reported by the candidate's browser; a reason to look closer on the scorecard, not proof.",
        "A person decides: don't reject automatically on this result.",
        "Scorecard: https://testee.ai/s/1",
    ]
    assert "below the passing grade" in result_comment("A", 40, False, False, "x", "en")
