from datetime import UTC, datetime
from types import SimpleNamespace
from uuid import uuid4

from rounds.constants.answer_patterns import FOLLOW_UPS, PatternSignal
from rounds.constants.rounds import RoundStatus
from rounds.helpers.integrity_report import answer_patterns, expected_seconds


def question(seconds: int = 60, difficulty: float | None = None, multi: bool = False) -> dict:
    return {
        "id": str(uuid4()),
        "text": f"Question {uuid4().hex[:6]}?",
        "options": [
            {"answer": "Right", "correct": True},
            {"answer": "Also right", "correct": multi},
            {"answer": "Wrong", "correct": False},
            {"answer": "Also wrong", "correct": False},
        ],
        "seconds": seconds,
        "difficulty": difficulty,
    }


def section(title: str, score: int, answers: list[tuple], status=RoundStatus.FINISHED):
    """A section whose answers are (question, correct, seconds); seconds None: timed out."""
    return SimpleNamespace(
        topic_title=title,
        final_score=score,
        status=status,
        questions=[q for q, _, _ in answers],
        answers=[
            SimpleNamespace(
                question_id=q["id"],
                correct=correct,
                timed_out=seconds is None,
                seconds=seconds,
                created_at=datetime.now(UTC),
            )
            for q, correct, seconds in answers
        ],
    )


def honest(title: str, score: int, count: int = 4) -> object:
    """Times that rise with each question's own time, half right."""
    answers = [(question(30 + 20 * i), i % 2 == 0, 10 + 15 * i) for i in range(count)]

    return section(title, score, answers)


def test_a_question_takes_longer_the_harder_it_is():
    assert expected_seconds(60, None) == 60
    assert expected_seconds(60, 1.0) == 60
    assert expected_seconds(60, 0.25) > expected_seconds(60, 0.75)


def test_nothing_before_every_section_is_finished():
    sections = [honest("SQL", 90), section("APIs", 0, [], status=RoundStatus.IN_PROGRESS)]

    assert answer_patterns(sections).model_dump() == {"signals": [], "follow_ups": []}
    assert answer_patterns([]).model_dump() == {"signals": [], "follow_ups": []}


def test_nothing_fired_means_no_signal_and_still_questions_to_ask():
    found = answer_patterns([honest("SQL", 90, 6), honest("APIs", 40, 6)])

    assert found.signals == []
    assert found.follow_ups


def test_follow_ups_come_from_the_strongest_topics_one_each_first_hardest_first():
    hard, easy = question(difficulty=0.2), question(difficulty=0.8)
    long_one, short_one = question(seconds=110), question(seconds=40)
    sections = [
        section("Weak", 30, [(question(), True, 20)]),
        section("Strong", 95, [(easy, True, 20), (hard, True, 20)]),
        section("Middle", 70, [(short_one, True, 20), (long_one, True, 20)]),
        section("Wrong only", 99, [(question(), False, 20)]),
    ]
    found = answer_patterns(sections).follow_ups

    assert len(found) == FOLLOW_UPS
    # One from each topic with a right answer, the strongest first; within one, the hardest (by
    # difficulty, else the longest time).
    assert [f.topic_title for f in found] == ["Strong", "Middle", "Weak"]
    assert [str(f.question_id) for f in found[:2]] == [hard["id"], long_one["id"]]


def test_a_follow_up_asks_about_every_right_option_against_a_wrong_one():
    multi = question(multi=True)
    found = answer_patterns([section("SQL", 100, [(multi, True, 30)])]).follow_ups[0]

    assert (found.topic_title, found.text) == ("SQL", multi["text"])
    assert found.right == ["Right", "Also right"]
    assert found.wrong == "Wrong"


def test_an_unusual_pattern_fires_with_its_counts_and_puts_its_hard_right_answers_first():
    hard = [(question(difficulty=0.2), True, 30 + i) for i in range(5)]
    easy = [(question(difficulty=0.9), i >= 3, 30 + i) for i in range(5)]
    # The candidate's strongest topic has only easy right answers.
    sections = [
        section("Easy topic", 100, [(question(difficulty=0.9), True, 25)]),
        section("Hard topic", 40, hard + easy),
    ]
    found = answer_patterns(sections)

    person_fit = [s for s in found.signals if s.kind == PatternSignal.PERSON_FIT]
    assert person_fit
    assert (person_fit[0].hard_right, person_fit[0].easy_wrong) == (5, 3)
    hard_ids = {q["id"] for q, _, _ in hard}
    assert str(found.follow_ups[0].question_id) in hard_ids


def test_flat_times_against_the_questions_fire_the_timing_signal():
    answers = [(question(seconds=30 + 12 * i), True, 30 - i % 7) for i in range(10)]
    found = answer_patterns([section("SQL", 100, answers)])

    assert [s.kind for s in found.signals] == [PatternSignal.TIMING]
    assert found.signals[0].hard is None
