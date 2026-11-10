"""Package de manipulation de pk et de tronçons."""

from importlib.metadata import PackageNotFoundError, version
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .conv import (
        ext_to_int,
        ext_to_m,
        int_to_ext,
        int_to_m,
        m_to_ext,
        m_to_int,
        rk_dm_to_ext,
        rk_dm_to_int,
    )
    from .tools import calcule_cc, self_intersect, zones_homogenes

try:
    __version__ = version("pktools")
except PackageNotFoundError:
    __version__ = "0.0.0"

__all__ = [
    "calcule_cc",
    "ext_to_int",
    "ext_to_m",
    "int_to_ext",
    "int_to_m",
    "m_to_ext",
    "m_to_int",
    "rk_dm_to_ext",
    "rk_dm_to_int",
    "self_intersect",
    "zones_homogenes",
]


def __getattr__(name: str):
    """Charger les fonctions Polars uniquement lorsqu'elles sont demandées."""
    if name not in __all__:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    from importlib import import_module

    module = ".tools" if name in {"calcule_cc", "self_intersect", "zones_homogenes"} else ".conv"
    value = getattr(import_module(module, __name__), name)
    globals()[name] = value
    return value


def __dir__() -> list[str]:
    return sorted(set(globals()) | set(__all__))
