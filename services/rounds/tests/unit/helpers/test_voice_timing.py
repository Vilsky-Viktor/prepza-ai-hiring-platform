from rounds.helpers.voice_timing import server_timing


def test_stages_are_a_server_timing_header_in_milliseconds():
    stages = {"transcribe": 0.8124, "match": 0.0, "total": 0.84}

    assert server_timing(stages) == "transcribe;dur=812, match;dur=0, total;dur=840"
