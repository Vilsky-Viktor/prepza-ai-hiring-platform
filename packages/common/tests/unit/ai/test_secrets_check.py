import pytest
from testee_common.ai.secrets_check import API, ATS, SLACK, find_secret

FAKE = "a8Kq3ZpL0vW7tYx2Rn5BdF9hJ4mC6sQe1Ug"


@pytest.mark.parametrize(
    "text, form",
    [
        (f"my key te_{FAKE}", API),
        (f"whsec_{FAKE}", API),
        ("xoxb-1234567890-abcdefghijkl", SLACK),
        ("https://hooks.slack.com/services/T0000/B0000/XXXXXXXXXXXXXXXXXXXXXXXX", SLACK),
        (f"sk-proj-{FAKE}", None),
        (f"sk-ant-api03-{FAKE}", None),
        (f"ghp_{FAKE}", None),
        (f"github_pat_11ABCDEFG_{FAKE}", None),
        (f"sk_live_{FAKE}", None),
        (f"pdl_live_apikey_{FAKE}", None),
        ("AKIAIOSFODNN7EXAMPLE", None),
        ("AIzaSyA-1234567890abcdefghijklmnopqrstu", None),
        (
            "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.dozjgNryP4J3jVmNHl0w5N_XgL0n3I9PlFUP0THsR8U",
            None,
        ),
        ("-----BEGIN RSA PRIVATE KEY-----\nMIIEow...", None),
        ("Greenhouse API token: 3f9a8b7c6d5e4f3a2b1c0d9e8f7a6b5c", ATS),
        ("password = hunter2hunter2hunter2", None),
        # An unknown kind of key, by how random it looks.
        (f"use this {FAKE}Zz9", None),
        # Seen on localhost: a secret without a known format, named by the message.
        ("Add my secret to Greenhouse ATS integration: 94uf9jf394ur0fj394g3ffh3", ATS),
        ("my greenhouse key is 7h3k9d2m5p8q1w4e", ATS),
        ("Hier ist mein Token: 7h3k9d2m5p8q1w4e6r", None),
        ("Мой токен для Workable: 7h3k9d2m5p8q1w4e6r", ATS),
        ("Пароль от Slack 7h3k9d2m5p8q1w4e", SLACK),
        # No word saying so, but letters and digits switching like a random value.
        ("please save 94uf9jf394ur0fj394g3ffh3 for later", None),
    ],
)
def test_secrets_are_found_with_the_form_they_belong_in(text, form):
    found = find_secret(text)

    assert found is not None
    assert found.form == form


@pytest.mark.parametrize(
    "text",
    [
        (
            "We're hiring a Senior Backend Engineer (Python): Django 5, PostgreSQL 16, Celery, "
            "Redis. Must have 5+ years, query tuning and idempotent payment flows."
        ),
        "Invite ann.lee+backend@example.com and bob@acme.co.uk to this interview",
        "https://www.acme.com/careers/senior-backend-engineer-python-django-postgresql?ref=x",
        "Open 8c1d2b8e-1a2b-4c3d-8e9f-0a1b2c3d4e5f and 11111111-2222-4333-8444-555555555555",
        "def get_token(user):\n    return jwt.encode({'sub': user.id}, settings.SECRET_KEY)",
        "Where do I put my Greenhouse API token?",
        "How do I reset my password?",
        "supercalifragilisticexpialidocious_antidisestablishmentarianism",
        "/companies/8c1d2b8e-1a2b-4c3d-8e9f-0a1b2c3d4e5f/interviews/11111111-2222-4333-8444",
        "Who passed the Backend developer interview this week, with a grade above 70%?",
        # Order ids, product codes and words glued to versions, with or without a "key" word.
        "Order ORD20231015000123 and invoice INV2024000123456789 were paid",
        "The product code is SKU20240012345ABCDEF",
        "Key skills: postgresql16django5celery, python3, kubernetes1.29",
        "Our API key question: where do I find interview 8c1d2b8e-1a2b-4c3d-8e9f-0a1b2c3d4e5f?",
        "Ключевые навыки: Python, Django, PostgreSQL",
    ],
)
def test_ordinary_messages_have_no_secret(text):
    assert find_secret(text) is None


def test_a_secret_anywhere_in_the_chat_sent_along_is_found():
    from testee_common.ai.secrets_check import secret_in

    assert secret_in(["Hi", f"here: ghp_{FAKE}"]).form is None
    assert secret_in(["Hi", "How much is it?"]) is None
