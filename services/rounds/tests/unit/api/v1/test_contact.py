def test_visitors_send_contact_messages(client, monkeypatch):
    saved = []

    async def fake_save(session, event_type, data):
        saved.append(data)

    async def fake_flush():
        return None

    monkeypatch.setattr("rounds.services.contact.sessions.add_event", fake_save)
    monkeypatch.setattr("rounds.services.contact.outbox_service.flush_quietly", fake_flush)
    body = {"name": " Ann ", "email": "ann@example.com", "message": "Do you offer invoices?"}

    response = client.post("/help/contact", json=body, headers={"Accept-Language": "de"})

    assert response.status_code == 204
    assert saved == [
        {
            "name": "Ann",
            "email": "ann@example.com",
            "message": "Do you offer invoices?",
            "language": "de",
        }
    ]


def test_contact_messages_are_limited_per_address_and_in_all(client, monkeypatch, redis):
    async def fake_save(session, event_type, data):
        return None

    async def fake_flush():
        return None

    monkeypatch.setattr("rounds.services.contact.sessions.add_event", fake_save)
    monkeypatch.setattr("rounds.services.contact.outbox_service.flush_quietly", fake_flush)
    body = {"name": "Ann", "email": "ann@example.com", "message": "Hi"}

    client.post("/help/contact", json=body)

    assert redis.counts == {"rate:contact:ip:testclient": 1, "rate:contact:all": 1}


def test_contact_messages_need_every_field(client):
    body = {"name": "Ann", "email": "ann@example.com", "message": "Hi"}

    assert client.post("/help/contact", json={**body, "email": "not-an-email"}).status_code == 422
    assert client.post("/help/contact", json={**body, "name": "  "}).status_code == 422
    assert client.post("/help/contact", json={**body, "message": ""}).status_code == 422
