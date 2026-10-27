import pytest
from prepza_common.db.schema_rules import _literals


@pytest.mark.parametrize(
    ("model", "database"),
    [
        (
            "status IN ('a', 'it''s')",
            (
                "CHECK (((status)::text = ANY ((ARRAY['a'::character varying, "
                "'it''s'::character varying])::text[])))"
            ),
        ),
        ("grade BETWEEN 0 AND 100", "CHECK (((grade >= 0) AND (grade <= 100)))"),
        ("vote IN (-1, 1)", "CHECK ((vote = ANY (ARRAY['-1'::integer, 1])))"),
    ],
)
def test_a_check_reads_the_same_however_postgres_rewrote_it(model, database):
    assert _literals(model) == _literals(database)


def test_a_value_added_in_the_code_makes_the_check_differ():
    database = "CHECK (((status)::text = ANY ((ARRAY['a'::character varying])::text[])))"

    assert _literals("status IN ('a', 'b')") != _literals(database)
