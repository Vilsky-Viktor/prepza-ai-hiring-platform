"""The help chat and its votes moved to the assistant: rounds' old addresses, kept one release,
send the browser there."""

import uuid


def test_the_old_help_chat_and_vote_addresses_send_the_browser_to_the_assistant(client):
    answer = uuid.uuid4()

    chat = client.post("/help/chat", json={}, follow_redirects=False)
    vote = client.put(f"/help/answers/{answer}/vote", json={}, follow_redirects=False)

    # 307 keeps the method and the body, so the browser asks the assistant the same.
    assert (chat.status_code, chat.headers["location"]) == (307, "/api/assistant/help/chat")
    assert (vote.status_code, vote.headers["location"]) == (
        307,
        f"/api/assistant/help/answers/{answer}/vote",
    )
