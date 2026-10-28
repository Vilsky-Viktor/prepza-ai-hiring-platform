from library.constants.quality import QualityFlag
from library.helpers.quality import flag_for, wrong_key

# A multi-answer question: two right options of four.
OPTIONS = [
    {"answer": "Debit cash", "correct": True},
    {"answer": "Credit revenue", "correct": True},
    {"answer": "Debit revenue", "correct": False},
    {"answer": "Credit expenses", "correct": False},
]


def picks(cash, revenue, wrong, other=10):
    return {
        "Debit cash": cash,
        "Credit revenue": revenue,
        "Debit revenue": wrong,
        "Credit expenses": other,
    }


def flag(answers, credit, option_picks):
    return flag_for(OPTIONS, answers, credit, option_picks, {}, 0, 0)


def test_a_wrong_option_picked_more_than_the_least_picked_right_one_flags_the_key():
    assert wrong_key(OPTIONS, picks(cash=30, revenue=15, wrong=16))
    assert not wrong_key(OPTIONS, picks(cash=30, revenue=15, wrong=15))


def test_a_single_answer_key_is_still_judged_by_its_one_right_option():
    single = [{**option, "correct": index == 0} for index, option in enumerate(OPTIONS)]

    assert wrong_key(single, picks(cash=20, revenue=21, wrong=1))
    assert not wrong_key(single, picks(cash=20, revenue=20, wrong=1))


def test_too_hard_reads_the_credit_earned():
    # 40 answers earning 5.5 points in all: under the 15% too-hard line (6).
    assert flag(40, 5.5, picks(cash=20, revenue=20, wrong=10)) == QualityFlag.REWRITE
    assert flag(40, 6.5, picks(cash=20, revenue=20, wrong=10)) is None


def test_too_easy_reads_the_credit_earned():
    # Every answer ticked a right option, yet partial credit keeps it under 95% (38 of 40).
    assert flag(40, 37.5, picks(cash=40, revenue=30, wrong=10)) is None
    assert flag(40, 38.5, picks(cash=40, revenue=40, wrong=10)) == QualityFlag.WEAK_OPTIONS
