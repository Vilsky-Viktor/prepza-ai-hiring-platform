import pytest

from rounds.helpers.linkedin import linkedin_profile


@pytest.mark.parametrize(
    ("text", "profile"),
    [
        ("https://www.linkedin.com/in/ann-lee", "https://www.linkedin.com/in/ann-lee"),
        ("linkedin.com/in/ann-lee/", "https://www.linkedin.com/in/ann-lee"),
        (" http://uk.linkedin.com/in/AnnLee99 ", "https://www.linkedin.com/in/AnnLee99"),
        ("https://www.linkedin.com/company/acme", None),
        ("https://www.linkedin.com/in/", None),
        ("https://evil.com/linkedin.com/in/ann-lee", None),
        ("https://linkedin.com.evil.com/in/ann-lee", None),
        ("https://www.linkedin.com/in/ann-lee?trk=x", None),
        ("ann-lee", None),
    ],
)
def test_only_a_linkedin_profiles_address_counts_kept_in_one_form(text, profile):
    assert linkedin_profile(text) == profile
