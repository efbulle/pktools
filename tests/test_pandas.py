import importlib.util
import random
import subprocess
import sys

import pandas as pd
import polars as pl
import pytest

import pktools as pk
from pktools import pandas as ppk


@pytest.mark.parametrize(
    ("name", "values"),
    [
        ("ext_to_int", ["4+514", "0-1373", "412B+795", "D+698", "E+1456", "H-125"]),
        ("ext_to_m", ["4+514", "0-1373", "412T+795", "D+698", "H-125"]),
        ("int_to_m", [-1000, -1373, -214, 456, 7400388, 41210795, 41220795, 41230795]),
        ("int_to_ext", [-1000, -1373, -214, 456, 7400388, 41210795, 41220795, 41230795]),
        ("m_to_int", [-1373, -214, 456, 1000, 74388, 413000]),
        ("m_to_ext", [-1373, -214, 456, 1000, 74388, 413000]),
    ],
)
def test_parity_single_argument(name, values):
    source = pd.Series(values, index=pd.Index(range(10, 10 + len(values)), name="ligne"), name="pk")
    expected = pl.DataFrame({"pk": values}).select(getattr(pk, name)(pl.col("pk")))["pk"].to_list()
    result = getattr(ppk, name)(source)
    assert result.tolist() == expected
    assert result.index.equals(source.index)
    assert result.name == source.name


@pytest.mark.parametrize("name", ["rk_dm_to_ext", "rk_dm_to_int"])
def test_parity_rk_dm(name):
    rk = pd.Series(["123", "0", "12", "12B", "D", "E"], name="rk")
    dm = pd.Series([62.0, -6.0, 1054.0, 1054.0, 698.0, 1456.0])
    expected = (
        pl.DataFrame({"rk": rk.tolist(), "dm": dm.tolist()})
        .select(getattr(pk, name)(pl.col("rk"), pl.col("dm")).alias("result"))["result"]
        .to_list()
    )
    assert getattr(ppk, name)(rk, dm).tolist() == expected


def test_large_varied_parity():
    rng = random.Random(123)
    prefixes = [str(n) for n in range(1000)] + list("DEFGH")
    values = [
        f"{rng.choice(prefixes)}{rng.choice(['', 'B', 'T', 'Q'])}"
        f"{rng.choice(['+', '-'])}{rng.randrange(10000):03d}"
        for _ in range(2000)
    ]
    source = pd.Series(values)
    internals = pl.DataFrame({"pk": values}).select(pk.ext_to_int(pl.col("pk")))["pk"]
    for name in ("ext_to_int", "ext_to_m"):
        expected = pl.DataFrame({"pk": values}).select(getattr(pk, name)(pl.col("pk")))["pk"]
        assert getattr(ppk, name)(source).tolist() == expected.to_list()
    for name in ("int_to_m", "int_to_ext"):
        if name == "int_to_ext":
            # Some valid external encodings produce an internal repère outside 0..3.
            internals_for_test = internals.filter((internals.abs() // 10000 % 10) <= 3)
        else:
            internals_for_test = internals
        expected = pl.DataFrame({"pk": internals_for_test}).select(getattr(pk, name)(pl.col("pk")))[
            "pk"
        ]
        assert (
            getattr(ppk, name)(pd.Series(internals_for_test.to_list())).tolist()
            == expected.to_list()
        )


@pytest.mark.parametrize("name", ["ext_to_int", "ext_to_m"])
@pytest.mark.parametrize(
    "bad", ["abc74+388xyz", "74+388\n", "12+12", "1234+567", "12+12345", "", 123, "１２+３４５"]
)
def test_invalid_external_values_are_identified(name, bad):
    values = pd.Series(["4+514", bad], index=["ok", "bad"])
    with pytest.raises(ValueError, match="bad"):
        getattr(ppk, name)(values)


@pytest.mark.parametrize("name", ["int_to_m", "int_to_ext", "m_to_int", "m_to_ext"])
@pytest.mark.parametrize("bad", [True, "123", 1.25, float("inf"), 2**64])
def test_invalid_numeric_values(name, bad):
    with pytest.raises(ValueError, match="bad"):
        getattr(ppk, name)(pd.Series([123, bad], index=["ok", "bad"], dtype=object))


def test_internal_complement_and_overflow_validation():
    with pytest.raises(ValueError, match="Complément"):
        ppk.int_to_ext(pd.Series([40000]))
    with pytest.raises(ValueError, match="limites"):
        ppk.m_to_int(pd.Series([92_233_720_368_548_000]))
    assert ppk.m_to_int(pd.Series([92_233_720_368_547_999])).iloc[0] == 9_223_372_036_854_700_999
    assert (
        ppk.m_to_int(pd.Series([-9_223_372_036_854_775_807])).iloc[0] == -9_223_372_036_854_775_807
    )


@pytest.mark.parametrize(
    ("name", "value", "dtype"),
    [
        ("ext_to_int", "4+514", "Int64"),
        ("ext_to_m", "4+514", "Int64"),
        ("int_to_m", 4514, "Int64"),
        ("int_to_ext", 4514, "string"),
        ("m_to_int", 4514, "Int64"),
        ("m_to_ext", 4514, "string"),
    ],
)
def test_missing_duplicate_index_and_dtype(name, value, dtype):
    source = pd.Series([value, None, pd.NA, float("nan")], index=["a", "a", "b", "b"], name="pk")
    result = getattr(ppk, name)(source)
    assert result.index.equals(source.index)
    assert result.name == "pk"
    assert str(result.dtype) == dtype
    assert result.iloc[1:].isna().all()


def test_rk_dm_missing_invalid_and_index():
    index = pd.Index(["a", "a", "b"])
    rk = pd.Series(["12", None, "D"], index=index, name="rk")
    dm = pd.Series([None, 42, 698], index=index)
    result = ppk.rk_dm_to_int(rk, dm)
    assert result.isna().tolist() == [True, True, False]
    assert result.iloc[2] == 698
    with pytest.raises(ValueError, match="index"):
        ppk.rk_dm_to_ext(rk, dm.reset_index(drop=True))
    with pytest.raises(ValueError, match="bad"):
        ppk.rk_dm_to_ext(pd.Series(["invalid"], index=["bad"]), pd.Series([None], index=["bad"]))
    with pytest.raises(ValueError, match="bad"):
        ppk.rk_dm_to_ext(pd.Series([None], index=["bad"]), pd.Series([10000], index=["bad"]))


@pytest.mark.parametrize("name", ["int_to_m", "int_to_ext", "m_to_int", "m_to_ext"])
@pytest.mark.parametrize("dtype", ["string", "boolean", "Int64"])
def test_all_missing_nullable_types(name, dtype):
    result = getattr(ppk, name)(pd.Series([pd.NA], dtype=dtype))
    assert result.isna().all()


def test_reject_non_series():
    with pytest.raises(TypeError, match="Series"):
        ppk.ext_to_m(["4+514"])  # type: ignore[arg-type]


@pytest.mark.parametrize("value", [[1, 2], {"a": 1}, object()])
def test_invalid_objects_report_their_row(value):
    with pytest.raises(ValueError, match="bad"):
        ppk.ext_to_m(pd.Series([value], index=["bad"]))
    with pytest.raises(ValueError, match="bad"):
        ppk.m_to_int(pd.Series([value], index=["bad"]))


def test_import_pandas_does_not_import_polars():
    script = (
        "import sys; from pktools.pandas import ext_to_m; import pandas as pd; "
        "assert 'polars' not in sys.modules; "
        "assert ext_to_m(pd.Series(['4+514'])).iloc[0] == 4514; "
        "assert 'polars' not in sys.modules"
    )
    subprocess.run([sys.executable, "-c", script], check=True)
    assert importlib.util.find_spec("pktools.pandas") is not None


def test_existing_polars_exports_are_discoverable():
    assert set(pk.__all__).issubset(dir(pk))
    for name in pk.__all__:
        assert callable(getattr(pk, name))
