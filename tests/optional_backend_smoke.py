"""Smoke checks run against a wheel installed with exactly one optional extra."""

import importlib.util
import sys

import pktools


def check_pandas() -> None:
    assert importlib.util.find_spec("polars") is None

    import pandas as pd

    from pktools import pandas as pk_pandas

    assert pk_pandas.ext_to_m(pd.Series(["4+514"])).iloc[0] == 4514
    try:
        pk_pandas.ext_to_m(pd.Series(["invalid"]))
    except ValueError:
        pass
    else:
        raise AssertionError("Invalid PK accepted")
    assert "polars" not in sys.modules

    try:
        polars_function = pktools.ext_to_m
    except ImportError as exc:
        assert "pktools[polars]" in str(exc)
        assert "git+https://github.com/efbulle/pktools.git@main" in str(exc)
    else:
        raise AssertionError(
            f"Missing Polars did not produce an installation hint: {polars_function}"
        )


def check_polars() -> None:
    assert importlib.util.find_spec("pandas") is None

    import polars as pl

    assert pl.DataFrame({"pk": ["4+514"]}).select(pktools.ext_to_m(pl.col("pk"))).item() == 4514
    from pktools.tools import calcule_cc

    assert callable(calcule_cc)
    assert "pandas" not in sys.modules


if __name__ == "__main__":
    if sys.argv[1:] == ["pandas"]:
        check_pandas()
    elif sys.argv[1:] == ["polars"]:
        check_polars()
    else:
        raise SystemExit("Usage: optional_backend_smoke.py pandas|polars")
