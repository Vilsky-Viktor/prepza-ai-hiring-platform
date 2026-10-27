from prepza_common.ai.examples import pool_share

from app.constants.sets import COMPANY_QUESTIONS, PRACTICE_QUESTIONS, Pool


def assign_pools(questions: list, share: float) -> None:
    """A new template topic's pools: questions reused from the bank are company questions; of
    the fresh ones, PRACTICE_QUESTIONS go to practice, with their share of multi-answer questions
    and of questions with an example (prepza_common.ai.examples.pool_share), and the rest to
    companies."""
    fresh = [question for question in questions if question.source_question_id is None]
    practice = pool_share(questions, fresh, PRACTICE_QUESTIONS, share)[0]

    for question in questions:
        question.pool = Pool.PRACTICE if question in practice else Pool.COMPANY


def missing(practice: int, company: int) -> tuple[int, int]:
    """The practice and company questions a topic lacks to hold what a template topic is meant
    to (PRACTICE_QUESTIONS, COMPANY_QUESTIONS)."""
    return max(PRACTICE_QUESTIONS - practice, 0), max(COMPANY_QUESTIONS - company, 0)
