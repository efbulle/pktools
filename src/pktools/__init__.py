"""Package de manipulation de pk et de tronçons."""

from importlib.metadata import PackageNotFoundError, version

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
