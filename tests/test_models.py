"""The model picker offered `claude-4.5-haiku`, which is not a real id, so
choosing Claude failed at call time. These checks are offline -- litellm ships a
registry of every model it routes, so no API key or network is needed."""

from typing import Any, cast

import litellm
import pytest

from text2ics.models import (
    DEFAULT_LABEL,
    DEFAULT_MODEL,
    DEFAULT_PROVIDER,
    KEY_URLS,
    PROVIDERS,
)

# litellm ships no types for this; pin it once here rather than at each use.
MODEL_COST = cast(
    "dict[str, dict[str, Any]]",
    litellm.model_cost,  # pyright: ignore[reportUnknownMemberType,reportUnknownArgumentType]
)

ALL_MODELS = [(p, label, mid) for p, ms in PROVIDERS.items() for label, mid in ms.items()]


def price(model_id: str) -> float:
    entry = MODEL_COST[model_id]
    return entry.get("input_cost_per_token", 0) + entry.get("output_cost_per_token", 0)


@pytest.mark.parametrize("provider,label,model_id", ALL_MODELS)
def test_offered_model_is_a_real_litellm_id(provider: str, label: str, model_id: str):
    assert model_id in MODEL_COST, (
        f"{provider}/{label}: {model_id!r} is not a litellm model id, "
        "so picking it in the app would fail"
    )


def test_default_is_the_cheapest_model_of_the_default_provider():
    assert DEFAULT_PROVIDER in PROVIDERS
    assert PROVIDERS[DEFAULT_PROVIDER][DEFAULT_LABEL] == DEFAULT_MODEL
    # The picker opens on index 0, so the default must be the first entry.
    assert next(iter(PROVIDERS[DEFAULT_PROVIDER])) == DEFAULT_LABEL


@pytest.mark.parametrize("provider", list(PROVIDERS))
def test_each_provider_is_ordered_cheapest_first(provider: str):
    """The picker opens on index 0 and labels say 'cheapest', so keep it true."""
    prices = [price(m) for m in PROVIDERS[provider].values()]
    assert prices == sorted(prices), dict(zip(PROVIDERS[provider], prices))


def test_every_provider_has_a_key_url():
    assert set(KEY_URLS) == set(PROVIDERS)
