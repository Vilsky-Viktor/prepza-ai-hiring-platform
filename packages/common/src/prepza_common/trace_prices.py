"""Our models' prices in Langfuse, so every traced call carries its cost there: Langfuse prices a
call from its model's definition, and it has none for our models. Each service that traces syncs
them when it starts (`sync_model_prices`), from ai_constants.MODEL_PRICES; a price that changed
replaces the old definition. Nothing without Langfuse; a failure is logged and tracing goes on
without costs. Needs the package's `langfuse` extra."""

import asyncio
import logging
import math
import re

from langfuse.api.commons.types.pricing_tier_input import PricingTierInput
from prepza_common.ai_constants import MODEL_PRICES
from prepza_common.trace_constants import MODELS_PAGE, PRICE_SYNC_SECONDS
from prepza_common.tracing import client, tracing_on

logger = logging.getLogger(__name__)
PER_TOKEN = 1e6


def prices_of(name: str) -> dict[str, float]:
    """A model's USD per token for each kind of usage Langfuse's LangChain callback reports:
    fresh input, cached input, output and reasoning (billed as output)."""
    fresh, cached, output = MODEL_PRICES[name]

    return {
        "input": fresh / PER_TOKEN,
        "input_cache_read": cached / PER_TOKEN,
        "output": output / PER_TOKEN,
        "output_reasoning": output / PER_TOKEN,
    }


def match_pattern(name: str) -> str:
    """The model's name, alone or with a dated version ("gpt-6-luna-2026-08-01")."""
    return rf"(?i)^({re.escape(name)})(-\d{{4}}-\d{{2}}-\d{{2}})?$"


def same_prices(model, wanted: dict[str, float]) -> bool:
    """The definition already has these prices (as Langfuse stores them, within rounding)."""
    have = {kind: price.price for kind, price in (model.prices or {}).items()}

    return have.keys() == wanted.keys() and all(
        math.isclose(have[kind], wanted[kind], rel_tol=1e-9) for kind in wanted
    )


def listed(models) -> list:
    """Every model definition in the project, Langfuse's own included, page by page."""
    found, page = [], 1

    while batch := models.list(page=page, limit=MODELS_PAGE).data:
        found += batch
        page += 1

        if len(batch) < MODELS_PAGE:
            break

    return found


def sync() -> None:
    models = client().api.models
    ours = {m.model_name: m for m in listed(models) if not m.is_langfuse_managed}

    for name in MODEL_PRICES:
        wanted = prices_of(name)
        found = ours.get(name)

        if found is not None and same_prices(found, wanted):
            continue

        if found is not None:
            models.delete(found.id)

        models.create(
            model_name=name,
            match_pattern=match_pattern(name),
            unit="TOKENS",
            pricing_tiers=[
                PricingTierInput(
                    name="Standard", is_default=True, priority=0, conditions=[], prices=wanted
                )
            ],
        )
        logger.info("Langfuse prices set for %s", name)


async def sync_model_prices() -> None:
    """Our models' prices in Langfuse, at most PRICE_SYNC_SECONDS at start-up; never raises."""
    if not tracing_on():
        return

    try:
        await asyncio.wait_for(asyncio.to_thread(sync), PRICE_SYNC_SECONDS)
    except Exception as error:  # noqa: BLE001 - tracing goes on without costs
        logger.warning("Couldn't set the models' prices in Langfuse: %s", type(error).__name__)
