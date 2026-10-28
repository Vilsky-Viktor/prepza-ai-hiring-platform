import pytest
from pydantic import ValidationError

from companies.constants.invites import COMPANY_NAME_TOO_SHORT
from companies.schemas.companies import CompanyCreate, CompanyRename
from companies.schemas.superadmin_companies import CompanyNameIn


@pytest.mark.parametrize("name", ["EY", "3M", " HP "])
def test_a_company_name_of_two_characters_is_fine(name):
    assert CompanyCreate(name=name).name == name.strip()
    assert CompanyRename(title=name).title == name.strip()
    assert CompanyNameIn(name=name).name == name.strip()


@pytest.mark.parametrize("name", ["", "A", "  A  ", "     "])
def test_a_shorter_company_name_is_refused_saying_why(name):
    for build in (
        lambda: CompanyCreate(name=name),
        lambda: CompanyRename(title=name),
        lambda: CompanyNameIn(name=name),
    ):
        with pytest.raises(ValidationError) as refused:
            build()

        assert COMPANY_NAME_TOO_SHORT in str(refused.value)
