"""Models offered for extraction, grouped by provider.

Shared by the CLI and the Streamlit picker so the two cannot drift apart.

The app asks for one API key, so the provider is picked first and only that
provider's models are then offered -- mixing them in a single list invited
choosing Claude while holding an OpenAI key.

Values are litellm model ids. ``tests/test_models.py`` checks every id against
litellm's registry: the picker previously offered ``claude-4.5-haiku``, which is
not a real id, so choosing Claude simply failed. Models are listed cheapest
first within each provider, which that test also enforces.
"""

PROVIDERS: dict[str, dict[str, str]] = {
    "OpenAI": {
        "GPT-5.6 Luna (fast & cheap)": "gpt-5.6-luna",
        "GPT-5.6 Terra": "gpt-5.6-terra",
        "GPT-5.6 Sol (most capable)": "gpt-5.6-sol",
    },
    "Anthropic": {
        "Claude Haiku 4.5 (cheapest)": "claude-haiku-4-5",
        "Claude Sonnet 5": "claude-sonnet-5",
        "Claude Opus 5 (most capable)": "claude-opus-5",
    },
    "DeepSeek": {
        "DeepSeek V4 Flash (cheapest)": "deepseek/deepseek-v4-flash",
        "DeepSeek V3.2": "deepseek/deepseek-v3.2",
        "DeepSeek V4 Pro": "deepseek/deepseek-v4-pro",
    },
    "Kimi": {
        "Kimi K2.5 (cheapest)": "moonshot/kimi-k2.5",
        "Kimi K2.6": "moonshot/kimi-k2.6",
        "Kimi Latest": "moonshot/kimi-latest",
    },
    "GLM": {
        "GLM 4.7 Flash (free)": "zai/glm-4.7-flash",
        "GLM 5": "zai/glm-5",
        "GLM 5.1 (most capable)": "zai/glm-5.1",
    },
    "Grok": {
        "Grok 4.1 Fast (cheapest)": "xai/grok-4-1-fast-non-reasoning",
        "Grok 4.3": "xai/grok-4.3",
        "Grok 4.5 (most capable)": "xai/grok-4.5",
    },
}

# The environment variable litellm reads for each provider. The CLI offers these
# as --api-key fallbacks; tests/test_models.py keeps the set aligned with
# PROVIDERS so a new provider cannot be added without one.
ENV_VARS: dict[str, str] = {
    "OpenAI": "OPENAI_API_KEY",
    "Anthropic": "ANTHROPIC_API_KEY",
    "DeepSeek": "DEEPSEEK_API_KEY",
    "Kimi": "MOONSHOT_API_KEY",
    "GLM": "ZAI_API_KEY",
    "Grok": "XAI_API_KEY",
}

# Where to get a key, shown next to the provider choice.
KEY_URLS: dict[str, str] = {
    "OpenAI": "https://platform.openai.com/settings/organization/api-keys",
    "Anthropic": "https://console.anthropic.com/settings/keys",
    "DeepSeek": "https://platform.deepseek.com/api_keys",
    "Kimi": "https://platform.moonshot.ai/console/api-keys",
    "GLM": "https://z.ai/manage-apikey/apikey-list",
    "Grok": "https://console.x.ai/",
}

# Extraction is an easy task, so the cheap tier is the sensible default.
DEFAULT_PROVIDER = "OpenAI"
DEFAULT_LABEL = "GPT-5.6 Luna (fast & cheap)"
DEFAULT_MODEL = PROVIDERS[DEFAULT_PROVIDER][DEFAULT_LABEL]
