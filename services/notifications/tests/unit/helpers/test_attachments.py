from notifications.helpers.attachments import pdf_name


def test_a_pdf_name_joins_its_parts_and_drops_what_breaks_a_file_name():
    assert pdf_name("Candidates report", "Backend") == "Candidates report – Backend.pdf"
    assert pdf_name("Report", "a/b:c*d") == "Report – a b c d.pdf"
    assert pdf_name("Report", "") == "Report.pdf"
    assert pdf_name("", "") == "report.pdf"
    assert len(pdf_name("x" * 300)) == 104
