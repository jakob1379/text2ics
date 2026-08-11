"""The model picker offered `claude-4.5-haiku`, which is not a real id, so
choosing Claude failed at call time.

Genuinely offline: conftest.py sets LITELLM_LOCAL_MODEL_COST_MAP so these assert
against the model map bundled with the pinned litellm. Without it litellm fetches
the map from GitHub, and ids the installed version cannot resolve would pass here
and then fail in front of a user."""

from typing import Any, cast

import litellm
import pytest

from text2ics.models import (
    DEFAULT_LABEL,
    DEFAULT_MODEL,
    DEFAULT_PROVIDER,
    ENV_VARS,
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


def test_every_provider_has_the_env_var_litellm_reads():
    """A provider without one is unreachable from the CLI.

    Pinned exactly, not by suffix: the bug this guards against was
    ``CLAUDE_API_KEY``, which litellm never reads but which a
    ``endswith("_API_KEY")`` check would happily accept.
    """
    assert ENV_VARS == {
        "OpenAI": "OPENAI_API_KEY",
        "Anthropic": "ANTHROPIC_API_KEY",
        "DeepSeek": "DEEPSEEK_API_KEY",
        "Kimi": "MOONSHOT_API_KEY",
        "GLM": "ZAI_API_KEY",
        "Grok": "XAI_API_KEY",
    }
    assert set(ENV_VARS) == set(PROVIDERS)
