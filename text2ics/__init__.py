import importlib
from typing import Any

__all__ = ["process_content"]


def __getattr__(name: str) -> Any:
    """
    Lazily import attributes to speed up CLI startup.
    """
    if name == "process_content":
        return importlib.import_module(
            ".converter", __package__
        ).process_content
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
