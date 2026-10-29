import random

import pytest

from rounds.helpers.question_times import add_times, fitted_seconds, limits, question_weight

OPTIONS = [{"answer": "Yes"}, {"answer": "No"}, {"answer": "Maybe"}, {"answer": "Never"}]


def question(text: str) -> dict:
    return {"id": "q", "text": text, "options": OPTIONS}


def draw(seed: int) -> list[float]:
    """A random candidate's weights: up to 40 questions, from a one-liner to a long example."""
    picker = random.Random(seed)

    return [picker.uniform(0.2, 6) for _ in range(picker.randint(1, 40))]


@pytest.mark.parametrize("seed", range(200))
@pytest.mark.parametrize("average", [20, 45, 60, 75, 113])
def test_times_add_up_exactly_and_stay_within_the_limits_for_any_draw(seed, average):
    weights = draw(seed)
    seconds = fitted_seconds(weights, average)
    low, high = limits(average)

    assert sum(seconds) == len(weights) * average
    assert all(low <= time <= high for time in seconds)


def test_a_longer_question_gets_more_time_and_what_the_limits_cut_goes_to_the_others():
    # The long one would get far over twice the average: it's held there, and the rest share it.
    seconds = fitted_seconds([1, 1, 1, 20], 60)

    assert seconds[3] == 120
    assert seconds[:3] == [40, 40, 40]


def test_the_seconds_left_by_rounding_go_to_the_longest_questions():
    # 3 × 61 = 183 in thirds of a second each: 61 each, but 1, 1 and 1.3 share it unevenly.
    seconds = fitted_seconds([1, 1, 1.3], 61)

    assert sum(seconds) == 183
    assert seconds[2] == max(seconds)
    assert seconds[2] - seconds[0] >= 1


def test_equal_questions_get_the_average():
    assert fitted_seconds([1] * 7, 60) == [60] * 7


@pytest.mark.parametrize(("average", "extra"), [(60, 0), (60, 25), (60, 50), (60, 100)])
def test_extra_time_raises_the_average_the_times_are_fitted_to(average, extra):
    """Companies sends the average with the candidate's extra time (candidate_seconds), so every
    question gets its share more and the total is exact."""
    with_extra = round(average * (100 + extra) / 100)
    questions = [question("Short?"), question("A longer question " * 12)]
    add_times(questions, with_extra)

    assert sum(item["seconds"] for item in questions) == 2 * with_extra


def test_a_question_with_code_gets_more_time_than_a_one_liner():
    code = "```python\n" + "\n".join(f"total = total + item_{i}" for i in range(15)) + "\n```"
    questions = [question("What does `len` return?"), question(f"What does this print?\n\n{code}")]
    add_times(questions, 60)

    assert questions[1]["seconds"] > 60 > questions[0]["seconds"]


@pytest.mark.parametrize(
    "text",
    [
        "Что вернёт функция len для пустого списка в Python при вызове?",
        "Pythonで空のリストに対してlenを呼ぶと何が返りますか？",
        "ما الذي تعيده الدالة len لقائمة فارغة في بايثون عند استدعائها؟",
        "len 函数对空列表返回什么？",
        "ฟังก์ชัน len คืนค่าอะไรสำหรับลิสต์ว่าง",
    ],
)
def test_questions_in_scripts_whose_words_cant_be_weighed_get_weight_one(text):
    assert question_weight(question(text)) == 1.0


def test_untimed_questions_get_no_time():
    questions = [question("Short?")]
    add_times(questions, None)
    add_times([], 60)

    assert "seconds" not in questions[0]
