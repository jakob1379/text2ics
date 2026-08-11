import os
import sys
from pathlib import Path

# Must be set before litellm is imported. Without it litellm fetches its model
# map from GitHub at import time, so tests/test_models.py would validate model
# ids against the *live* registry and quietly pass for ids the pinned version
# cannot actually resolve -- and would fail outright with no network.
os.environ.setdefault("LITELLM_LOCAL_MODEL_COST_MAP", "True")

# app/ uses flat imports (`from utils import ...`), the layout Streamlit runs it
# with, so it is importable only with app/ on the path.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "app"))
