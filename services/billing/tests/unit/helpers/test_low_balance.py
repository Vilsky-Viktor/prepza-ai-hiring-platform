from billing.constants.credits import CANDIDATE_CREDITS
from billing.helpers.wallets import balance_out
from billing.models.billing import Wallet


def test_a_company_runs_low_when_the_next_candidate_isnt_covered():
    short = CANDIDATE_CREDITS - 2
    covered = CANDIDATE_CREDITS

    assert balance_out(Wallet(owner_type="company", owner_id="acme", balance=short, reserved=0)).low
    assert not balance_out(
        Wallet(owner_type="company", owner_id="acme", balance=covered + 600, reserved=600)
    ).low


def test_a_balance_says_how_many_candidates_it_pays_for():
    wallet = Wallet(owner_type="company", owner_id="acme", balance=1600, reserved=100)

    # 1,500 available, 500 a candidate.
    assert balance_out(wallet).candidates == 3
    assert (
        balance_out(Wallet(owner_type="company", owner_id="x", balance=0, reserved=0)).candidates
        == 0
    )
