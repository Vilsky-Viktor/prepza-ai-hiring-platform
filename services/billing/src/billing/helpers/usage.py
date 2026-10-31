from testee_common.ai.ai_constants import TESTEE_ACTIONS, Category


def category_of(action: str, company_id: str | None, paid: bool) -> Category:
    """Who an AI call was for: a company that had topped up by then pays, one that hadn't
    doesn't; without a company, testee's own work or a visitor's."""
    if company_id:
        return Category.PAID if paid else Category.UNPAID

    return Category.TESTEE if action in TESTEE_ACTIONS else Category.NO_COMPANY
