"""Conversions strictes de séries pandas, sans dépendance à Polars."""

from numbers import Integral
from typing import Any

import numpy as np
import pandas as pd
from pandas.api.types import is_bool_dtype, is_integer_dtype

from ._rules import COMP_MAP, OP_MAP, REGEX_PK_EXT, RER_C

_INT_MAX = 2**63 - 1
_M_MAX = (_INT_MAX // 100_000) * 1000 + 999
_FLOAT_EXACT_MAX = 2**53
_RK_PATTERN = r"(?:[0-9]{1,3}|[DEFGH])[BTQ]?"
# Python's \d also matches non-ASCII digits that Polars cannot cast to integers.
_EXT_PATTERN = REGEX_PK_EXT.replace(r"\d", "[0-9]")

__all__ = [
    "ext_to_int",
    "ext_to_m",
    "int_to_ext",
    "int_to_m",
    "m_to_ext",
    "m_to_int",
    "rk_dm_to_ext",
    "rk_dm_to_int",
]


def _series(values: pd.Series) -> None:
    if not isinstance(values, pd.Series):
        raise TypeError("Une pandas.Series est attendue")


def _invalid(values: pd.Series, mask: pd.Series, reason: str) -> None:
    mask = mask.fillna(False)
    if mask.any():
        positions = [i for i, bad in enumerate(mask) if bad]
        examples = [(i, values.index[i], values.iloc[i]) for i in positions[:10]]
        raise ValueError(
            f"{reason} : (position, index, valeur) {examples!r}; total={len(positions)}"
        )


def _integers(values: pd.Series, lower: int, upper: int) -> pd.Series:
    _series(values)
    missing = values.isna()
    if missing.all():
        return pd.Series(pd.NA, index=values.index, name=values.name, dtype="Int64")
    if is_bool_dtype(values.dtype):
        valid_type = pd.Series(False, index=values.index)
    elif is_integer_dtype(values.dtype):
        valid_type = pd.Series(True, index=values.index)
    else:

        def valid_number(x: Any) -> bool:
            return bool(
                isinstance(x, Integral)
                and not isinstance(x, bool)
                or isinstance(x, (float, np.floating))
                and -_FLOAT_EXACT_MAX <= x <= _FLOAT_EXACT_MAX
                and x == int(x)
            )

        valid_type = values.map(valid_number)
    _invalid(values, ~missing & ~valid_type, "Entier invalide")
    # Comparisons precede casting so out-of-range values cannot wrap.
    numeric = values.where(~missing, 0)
    _invalid(values, ~missing & ((numeric < lower) | (numeric > upper)), "Entier hors limites")
    return numeric.astype("Int64").mask(missing)


def _strings(values: pd.Series, pattern: str, reason: str) -> pd.Series:
    _series(values)
    missing = values.isna()
    types = values.map(lambda x: isinstance(x, str))
    _invalid(values, ~missing & ~types, reason)
    text = values.astype("string")
    _invalid(values, ~missing & ~text.str.fullmatch(pattern, na=False), reason)
    return text


def ext_to_int(pk_ext: pd.Series) -> pd.Series:
    """Convertir des PK externes strictement valides en entiers internes."""
    text = _strings(pk_ext, _EXT_PATTERN, "PK externe invalide")
    groups = text.str.extract(_EXT_PATTERN)
    add1 = groups["add1"].replace(RER_C).astype("Int64")
    comp = groups["comp"].map(COMP_MAP).astype("Int64")
    op = groups["op"].map(OP_MAP).astype("Int64")
    add2 = groups["add2"].astype("Int64")
    return (add1 * 100_000 + comp * 10_000 + op * add2).rename(pk_ext.name)


def int_to_m(pk_internes: pd.Series) -> pd.Series:
    """Convertir des PK internes en mètres, avec perte du complément."""
    values = _integers(pk_internes, -_INT_MAX, _INT_MAX)
    absolute = values.abs()
    rk = absolute // 100_000
    repere = absolute // 10_000 % 10
    offset = absolute % 10_000
    offset = offset.where(values >= 0, -offset)
    return (rk * 1000 + repere * 1000 + offset).rename(pk_internes.name)


def int_to_ext(pk_internes: pd.Series) -> pd.Series:
    """Convertir des PK internes en PK externes."""
    values = _integers(pk_internes, -_INT_MAX, _INT_MAX)
    absolute = values.abs()
    repere = absolute // 10_000 % 10
    _invalid(pk_internes, repere.notna() & (repere > 3), "Complément interne invalide")
    rk = (absolute // 100_000).astype("string")
    comp = repere.map({v: k for k, v in COMP_MAP.items()}).astype("string")
    hundreds = absolute % 1000
    sign = pd.Series("+", index=values.index, dtype="string").mask(
        (values < 0) & (hundreds > 0), "-"
    )
    offset = (absolute % 10_000).astype("string").str.zfill(3)
    return (rk + comp + sign + offset).rename(pk_internes.name)


def m_to_int(pk_m: pd.Series) -> pd.Series:
    """Convertir des mètres en PK internes."""
    values = _integers(pk_m, -_INT_MAX, _M_MAX)
    positive = values.clip(lower=0)
    result = (positive // 1000 * 100_000 + positive % 1000).where(values >= 0, values)
    return result.rename(pk_m.name)


def ext_to_m(pk_ext: pd.Series) -> pd.Series:
    """Convertir des PK externes en mètres."""
    return int_to_m(ext_to_int(pk_ext))


def m_to_ext(pk_m: pd.Series) -> pd.Series:
    """Convertir des mètres en PK externes."""
    return int_to_ext(m_to_int(pk_m))


def rk_dm_to_ext(rk: pd.Series, dm: pd.Series) -> pd.Series:
    """Convertir des séries de repères et distances en PK externes."""
    _series(rk)
    _series(dm)
    if not rk.index.equals(dm.index):
        raise ValueError("Les index de rk et dm doivent être identiques")
    prefix = _strings(rk, _RK_PATTERN, "Repère invalide")
    distance = _integers(dm, -9999, 9999)
    sign = pd.Series("+", index=dm.index, dtype="string").mask(distance < 0, "-")
    return (prefix + sign + distance.abs().astype("string").str.zfill(3)).rename(rk.name)


def rk_dm_to_int(rk: pd.Series, dm: pd.Series) -> pd.Series:
    """Convertir des séries de repères et distances en PK internes."""
    return ext_to_int(rk_dm_to_ext(rk, dm))
