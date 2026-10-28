from types import SimpleNamespace

from companies.helpers.notifications import candidate_finished


def test_a_finished_candidate_carries_their_results_page():
    """Slack's "candidate finished" opens the candidate's results; the bell keeps the interview."""
    interview = SimpleNamespace(id="i1", company_id="c1", title="Backend")
    event = candidate_finished(interview, "v1", "a@b.c", 80)

    assert event["link"] == "/companies/c1/interviews/i1"
    assert event["data"]["candidate_link"] == "/companies/c1/interviews/i1/candidates/v1"
