"""What leaves us for Sentry and Langfuse (prepza_common.scrub): no emails, URLs cut to their
host, and for Langfuse people's names too."""

from prepza_common.scrub import scrub, scrub_people
from pydantic import BaseModel


def test_emails_are_scrubbed_everywhere_in_an_event():
    event = {
        "message": "Invite to bob@example.com failed",
        "exception": {"values": [{"value": "No inbox for Ann.Lee+jobs@mail.co.uk"}]},
        "breadcrumbs": [{"data": {"email": "carol@example.org", "count": 3}}],
    }

    assert scrub(event) == {
        "message": "Invite to [email] failed",
        "exception": {"values": [{"value": "No inbox for [email]"}]},
        "breadcrumbs": [{"data": {"email": "[email]", "count": 3}}],
    }


def test_urls_keep_only_their_scheme_and_host_and_queries_are_dropped():
    hook = "https://hooks.slack.com/services/T0/B0/secret"
    event = {
        "request": {"url": "https://api.prepza.com/invites/token123", "query_string": "t=1"},
        "breadcrumbs": [
            {"category": "httplib", "data": {"url": hook, "http.query": "key=1"}},
        ],
        "spans": [{"description": f"POST {hook}", "data": {"url": "http://a:b@x.io:8080/p?q"}}],
        "exception": {"values": [{"value": f"Client error '404 Not Found' for url '{hook}'"}]},
    }

    assert scrub(event) == {
        "request": {"url": "https://api.prepza.com"},
        "breadcrumbs": [{"category": "httplib", "data": {"url": "https://hooks.slack.com"}}],
        "spans": [
            {"description": "POST https://hooks.slack.com", "data": {"url": "http://x.io:8080"}}
        ],
        "exception": {
            "values": [{"value": "Client error '404 Not Found' for url 'https://hooks.slack.com'"}]
        },
    }


def test_names_and_emails_in_a_tools_json_result_are_masked():
    result = '{"id": "c1", "name": "Ann Lee", "email": "ann@example.com", "candidate_name": "Bo"}'

    assert (
        scrub_people(result)
        == '{"id": "c1", "name": "[person]", "email": "[person]", "candidate_name": "[person]"}'
    )


def test_name_fields_of_data_and_hidden_names_are_masked_and_the_rest_kept():
    class Candidate(BaseModel):
        name: str
        grade: int

    data = {
        "messages": [
            {"role": "system", "content": r'The user is "Jos\u00e9 Ruiz".'},
            {"role": "user", "content": "Send José Ruiz's link https://prepza.com/i/tok3n"},
        ],
        "candidate": Candidate(name="Bo", grade=3),
        "update": {"candidate_name": "Cy", "title": "Backend"},
        "steps": ("a", 2, None, True),
    }

    assert scrub_people(data, ("José Ruiz", r"Jos\u00e9 Ruiz")) == {
        "messages": [
            {"role": "system", "content": 'The user is "[person]".'},
            {"role": "user", "content": "Send [person]'s link https://prepza.com"},
        ],
        "candidate": {"name": "[person]", "grade": 3},
        "update": {"candidate_name": "[person]", "title": "Backend"},
        "steps": ["a", 2, None, True],
    }


def test_a_hidden_name_is_masked_only_as_a_whole_word():
    assert scrub_people("Ann's annual review", ("Ann",)) == "[person]'s annual review"
