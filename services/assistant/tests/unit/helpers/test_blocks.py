from assistant.helpers.blocks import link, render_block

COMPANY = "8c1d2b8e-1a2b-4c3d-8e9f-0a1b2c3d4e5f"
INTERVIEW = "3f2b6a1e-8a7c-4c1e-9a55-0b6f3c2d1e00"
CANDIDATE_LINK = "/companies/{company_id}/interviews/{interview_id}/candidates/{id}"


def test_links_are_filled_from_ids_only():
    values = {"company_id": COMPANY, "interview_id": INTERVIEW, "id": "c1"}

    assert (
        link(CANDIDATE_LINK, values) == f"/companies/{COMPANY}/interviews/{INTERVIEW}/candidates/c1"
    )
    assert link("/faq", {}) == "/faq"
    assert link(None, values) is None


def test_text_never_becomes_a_link():
    for bad in ["https://evil.example", "../settings", "a b", "x/y", "", True, None]:
        assert link("/companies/{company_id}/members", {"company_id": bad}) is None


def test_item_blocks_link_each_item():
    rows = [{"id": "c1", "email": "ann@example.com"}, {"id": "bad id", "email": "bob@example.com"}]
    block = render_block(
        "candidate_rows", CANDIDATE_LINK, rows, {"company_id": COMPANY, "interview_id": INTERVIEW}
    )

    assert block == {
        "kind": "candidate_rows",
        "items": rows,
        "links": [f"/companies/{COMPANY}/interviews/{INTERVIEW}/candidates/c1", None],
    }


def test_a_link_block_is_one_link_and_no_render_is_no_block():
    context = {"company_id": COMPANY}

    assert render_block("link", "/companies/{company_id}/members", [{"id": "m"}], context) == {
        "kind": "link",
        "items": [],
        "links": [f"/companies/{COMPANY}/members"],
    }
    assert render_block("link", "/companies/{company_id}/members", {}, {"company_id": None}) == {
        "kind": "link",
        "items": [],
        "links": [],
    }
    assert render_block(None, "/faq", {"a": 1}, context) is None
