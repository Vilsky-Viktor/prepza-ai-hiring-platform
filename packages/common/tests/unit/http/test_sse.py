import asyncio

from testee_common.http.sse import KEEP_ALIVE, event_stream, sse_event


def test_an_event_is_one_data_line_of_json_and_a_blank_line():
    assert sse_event({"delta": "Hi ü"}) == 'data: {"delta": "Hi \\u00fc"}\n\n'
    assert KEEP_ALIVE.startswith(":")


def test_a_stream_is_unbuffered_server_sent_events():
    async def events():
        yield sse_event({"done": True})

    response = event_stream(events())

    assert response.media_type == "text/event-stream"
    assert response.headers["X-Accel-Buffering"] == "no"
    assert response.headers["Cache-Control"] == "no-store"

    async def body():
        return [chunk async for chunk in response.body_iterator]

    assert asyncio.run(body()) == ['data: {"done": true}\n\n']
