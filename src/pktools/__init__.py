"""
Package de manipulation de pk et de tronçons.
"""

from importlib.metadata import version

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

__version__ = version("pktools")

__all__ = [
    "int_to_m",
    "int_to_ext",
    "ext_to_int",
    "m_to_int",
    "ext_to_m",
    "m_to_ext",
    "rk_dm_to_ext",
    "rk_dm_to_int",
    "calcule_cc",
    "self_intersect",
    "zones_homogenes",
]
