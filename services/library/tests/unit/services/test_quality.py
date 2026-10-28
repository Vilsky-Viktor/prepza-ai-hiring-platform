import asyncio
import uuid
from types import SimpleNamespace

from library.constants.quality import QualityFlag
from library.helpers.quality import flag_for
from library.integrations import generation
from library.repositories import preparations, quality
from library.services import outbox
from library.services.quality import review

QUESTION_ID = uuid.uuid4()
OPTIONS = [
    {"answer": "Debit cash", "correct": True},
    {"answer": "Credit cash", "correct": False},
    {"answer": "Debit revenue", "correct": False},
    {"answer": "Credit expenses", "correct": False},
]


def flag(answers=0, correct=0, picks=None, reports=None, likes=0, dislikes=0):
    return flag_for(OPTIONS, answers, correct, picks or {}, reports or {}, likes, dislikes)


def even_picks(right):
    """`right` picks of the correct option and 10 of each wrong one."""
    return {"Debit cash": right, "Credit cash": 10, "Debit revenue": 10, "Credit expenses": 10}


def test_a_new_question_is_not_flagged():
    assert flag() is None
    assert flag(answers=10, correct=0, picks={"Credit cash": 10}) is None


def test_a_wrong_option_beating_the_key_flags_it():
    picks = {"Debit cash": 8, "Credit cash": 20, "Debit revenue": 1, "Credit expenses": 1}

    assert flag(answers=30, correct=8, picks=picks) == QualityFlag.WRONG_KEY


def test_two_wrong_answer_reports_flag_the_key():
    assert flag(reports={"wrong_answer": 2}) == QualityFlag.WRONG_KEY
    assert flag(reports={"wrong_answer": 1}) is None


def test_unclear_hard_to_read_off_topic_and_disliked_questions_are_rewritten():
    assert flag(reports={"unclear": 2}) == QualityFlag.REWRITE
    assert flag(reports={"hard_to_read": 2}) == QualityFlag.REWRITE
    assert flag(reports={"hard_to_read": 1}) is None
    assert flag(reports={"off_topic": 2}) == QualityFlag.REWRITE
    assert flag(likes=1, dislikes=3) == QualityFlag.REWRITE
    assert flag(likes=2, dislikes=3) is None


def test_too_hard_is_rewritten():
    picks = {"Debit cash": 4, "Credit cash": 4, "Debit revenue": 4, "Credit expenses": 4}

    assert flag(answers=40, correct=4, picks=picks) == QualityFlag.REWRITE


def test_dead_or_too_easy_options_are_weak():
    dead = {"Debit cash": 30, "Credit cash": 10, "Debit revenue": 10, "Credit expenses": 0}

    assert flag(answers=50, correct=30, picks=dead) == QualityFlag.WEAK_OPTIONS
    assert flag(answers=60, correct=30, picks=even_picks(30)) is None


def stored(flag=None, kept=False, answers=0):
    question = SimpleNamespace(text="Which entry records a cash sale?", options=OPTIONS)
    stats = SimpleNamespace(
        strong_answers=0,
        strong_correct=0,
        weak_answers=0,
        weak_correct=0,
        timeouts=0,
        answers=answers,
        correct=0,
        option_picks={},
        flag=flag,
        kept=kept,
    )

    return question, stats, {"wrong_answer": 2}, 0, 0


def record(monkeypatch, found, generation_down=False):
    calls = []

    async def fake_load(_question_id):
        return found

    async def fake_verify(question_id, flag):
        if generation_down:
            raise ConnectionError("generation is down")

        calls.append(("verify", flag))

    async def fake_save(question_id, flag, kept=False, notice=None):
        calls.append(("save", flag))

    async def fake_change(question_id, previous, flag, notice=None):
        calls.append(("save", flag))

        return True

    async def fake_set(_question_id):
        return SimpleNamespace(id=uuid.uuid4(), owner_type="user", owner_id="u1", title="Kit")

    async def fake_topic(_question_id):
        return "Bookkeeping"

    async def fake_flush():
        pass

    monkeypatch.setattr(quality, "load", fake_load)
    monkeypatch.setattr(generation, "verify_question", fake_verify)
    monkeypatch.setattr(quality, "save_flag", fake_save)
    monkeypatch.setattr(quality, "change_flag", fake_change)
    monkeypatch.setattr(preparations, "get_for_question", fake_set)
    monkeypatch.setattr(preparations, "topic_of_question", fake_topic)
    monkeypatch.setattr(outbox, "flush_quietly", fake_flush)

    return calls


def test_a_new_flag_is_saved_then_goes_to_the_verifier(monkeypatch):
    """Saved first, so the verifier finds the flag it's asked to act on."""
    calls = record(monkeypatch, stored())

    asyncio.run(review(QUESTION_ID))

    assert calls == [("save", QualityFlag.WRONG_KEY), ("verify", QualityFlag.WRONG_KEY)]


def test_a_known_flag_is_not_sent_again(monkeypatch):
    calls = record(monkeypatch, stored(flag=QualityFlag.WRONG_KEY))

    asyncio.run(review(QUESTION_ID))

    assert calls == []


def test_a_kept_question_is_never_flagged(monkeypatch):
    calls = record(monkeypatch, stored(kept=True))

    asyncio.run(review(QUESTION_ID))

    assert calls == []


def test_a_flag_stays_saved_when_the_verifier_is_unreachable(monkeypatch):
    """The daily sweep (resend_stale_flags) sends it again."""
    calls = record(monkeypatch, stored(), generation_down=True)

    asyncio.run(review(QUESTION_ID))

    assert calls == [("save", QualityFlag.WRONG_KEY)]


def test_marking_wrong_again_while_the_check_waits_changes_nothing(monkeypatch):
    from library.services.quality import mark_wrong

    calls = record(monkeypatch, stored())
    current = {"flag": None}

    async def current_flag(_question_id):
        return current["flag"]

    async def change(question_id, previous, flag, notice=None):
        current["flag"] = flag
        calls.append(("save", flag))

        return True

    monkeypatch.setattr(quality, "current_flag", current_flag)
    monkeypatch.setattr(quality, "change_flag", change)

    asyncio.run(mark_wrong(QUESTION_ID))
    asyncio.run(mark_wrong(QUESTION_ID))

    assert calls == [("save", QualityFlag.WRONG_KEY), ("verify", QualityFlag.WRONG_KEY)]


def test_flags_left_unfixed_go_to_the_verifier_again(monkeypatch):
    from datetime import UTC, datetime, timedelta

    from library.constants.quality import FLAG_RESEND_AFTER_HOURS, MAX_FLAG_RESENDS
    from library.services.quality import resend_stale_flags

    calls = record(monkeypatch, stored(), generation_down=False)
    asked = []

    async def take_stale_flags(before, limit):
        asked.append((before, limit))

        return [(QUESTION_ID, QualityFlag.REWRITE)]

    monkeypatch.setattr(quality, "take_stale_flags", take_stale_flags)

    assert asyncio.run(resend_stale_flags()) == 1

    [(before, limit)] = asked
    expected = datetime.now(UTC) - timedelta(hours=FLAG_RESEND_AFTER_HOURS)
    assert abs((before - expected).total_seconds()) < 5
    assert limit == MAX_FLAG_RESENDS
    assert calls == [("verify", QualityFlag.REWRITE)]


def stats_of(**counts):
    base = {
        "answers": 0,
        "timeouts": 0,
        "strong_answers": 0,
        "strong_correct": 0,
        "weak_answers": 0,
        "weak_correct": 0,
    }

    return SimpleNamespace(**(base | counts))


def test_a_question_strong_and_weak_candidates_get_right_alike_says_nothing():
    from library.helpers.quality import no_separation

    # Strong get it right 80% of the time, weak 75%: no real difference.
    assert no_separation(
        stats_of(strong_answers=20, strong_correct=16, weak_answers=20, weak_correct=15)
    )
    # 80% against 40%: it tells them apart.
    assert not no_separation(
        stats_of(strong_answers=20, strong_correct=16, weak_answers=20, weak_correct=8)
    )
    # Too few answers in a group to judge.
    assert not no_separation(
        stats_of(strong_answers=20, strong_correct=16, weak_answers=5, weak_correct=5)
    )


def test_a_question_time_runs_out_on_too_often_is_too_slow():
    from library.helpers.quality import too_slow

    assert too_slow(stats_of(answers=30, timeouts=10))
    assert not too_slow(stats_of(answers=36, timeouts=4))
    assert not too_slow(stats_of(answers=5, timeouts=5))


def test_a_candidates_group_follows_their_topic_score():
    from library.helpers.quality import score_group

    assert [score_group(score) for score in (90, 70, 55, 40, 10, None)] == [
        "strong",
        "strong",
        None,
        "weak",
        "weak",
        None,
    ]
