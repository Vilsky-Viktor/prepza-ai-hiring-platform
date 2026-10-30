"""Our models' prices in Langfuse (prepza_common.ai.trace_prices): set once, replaced when a price
changes, nothing without Langfuse, and a failure never stops a start. Langfuse's API is a fake."""

import asyncio
import re
from types import SimpleNamespace

import pytest
from prepza_common.ai import trace_prices
from prepza_common.ai.ai_constants import MODEL_PRICES


class Models:
    """Langfuse's model definitions: `rows` listed a page at a time; what was made and deleted."""

    def __init__(self, rows):
        self.rows = rows
        self.made = []
        self.deleted = []

    def list(self, page, limit):
        return SimpleNamespace(data=self.rows[(page - 1) * limit : page * limit])

    def create(self, **kwargs):
        self.made.append(kwargs)

    def delete(self, model_id):
        self.deleted.append(model_id)


def ours(name, prices, model_id="m1"):
    priced = {kind: SimpleNamespace(price=value) for kind, value in prices.items()}

    return SimpleNamespace(id=model_id, model_name=name, is_langfuse_managed=False, prices=priced)


@pytest.fixture
def langfuse(monkeypatch):
    def install(rows):
        models = Models(rows)
        monkeypatch.setattr(
            trace_prices, "client", lambda: SimpleNamespace(api=SimpleNamespace(models=models))
        )
        monkeypatch.setattr(trace_prices, "tracing_on", lambda: True)

        return models

    return install


def test_each_model_gets_its_prices_per_token_with_cached_input_and_reasoning(langfuse):
    managed = [SimpleNamespace(model_name="gpt-5", is_langfuse_managed=True)] * 150
    models = langfuse(managed)

    asyncio.run(trace_prices.sync_model_prices())

    assert [made["model_name"] for made in models.made] == list(MODEL_PRICES)
    [luna] = [made for made in models.made if made["model_name"] == "gpt-6-luna"]
    [tier] = luna["pricing_tiers"]
    assert tier.prices == pytest.approx(
        {"input": 0.1e-6, "input_cache_read": 0.01e-6, "output": 0.5e-6, "output_reasoning": 0.5e-6}
    )


def test_a_dated_version_matches_its_model():
    pattern = trace_prices.match_pattern("gpt-6.1-sol")

    assert re.match(pattern, "gpt-6.1-sol-2026-08-01")
    assert not re.match(pattern, "gpt-6x1-sol")


def test_prices_already_set_stay_and_a_changed_price_replaces_its_definition(langfuse):
    rows = [ours(name, trace_prices.prices_of(name)) for name in MODEL_PRICES]
    rows[0] = ours(rows[0].model_name, {"input": 1.0}, model_id="old")
    models = langfuse(rows)

    asyncio.run(trace_prices.sync_model_prices())

    assert models.deleted == ["old"]
    assert [made["model_name"] for made in models.made] == [rows[0].model_name]


def test_nothing_without_langfuse_and_a_failure_never_raises(monkeypatch):
    monkeypatch.setattr(trace_prices, "tracing_on", lambda: False)
    monkeypatch.setattr(trace_prices, "client", lambda: pytest.fail("called"))
    asyncio.run(trace_prices.sync_model_prices())

    def down():
        raise ConnectionError

    monkeypatch.setattr(trace_prices, "tracing_on", lambda: True)
    monkeypatch.setattr(trace_prices, "client", down)
    asyncio.run(trace_prices.sync_model_prices())
