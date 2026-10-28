def test_the_service_is_ready_once_it_reaches_its_database(client):
    response = client.get("/ready")

    assert (response.status_code, response.json()) == (200, {"status": "ready"})
