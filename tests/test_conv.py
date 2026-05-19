import polars as pl

import pktools as pk


def test_conv():
    pk_df = pl.DataFrame(
        [
            ("0-1373", -1373, -1373),
            ("0-214", -214, -214),
            ("0+456", 456, 456),
            ("0+1373", 1373, 1373),
            ("74+388", 7400388, 74388),
            ("234+251", 23400251, 234251),
            ("412+1025", 41201025, 413025),
            ("412B+795", 41210795, 413795),
            ("412T+795", 41220795, 414795),
            ("412Q+795", 41230795, 415795),
        ],
        orient="row",
        schema=["pk_ext", "pk_int", "pk_m"],
    ).with_columns(
        pk.int_to_ext(pl.col("pk_int")).alias("pk_ext2"),
        pk.int_to_m(pl.col("pk_int")).alias("pk_m2"),
        pk.ext_to_int(pl.col("pk_ext")).alias("pk_int2"),
        pk.ext_to_m(pl.col("pk_ext")).alias("pk_m3"),
    )
    assert pk_df["pk_m"].equals(pk_df["pk_m2"])
    assert pk_df["pk_ext"].equals(pk_df["pk_ext2"])
    assert pk_df["pk_int"].equals(pk_df["pk_int2"])
    assert pk_df["pk_m3"].equals(pk_df["pk_m"])


def test_conv_anom():
    pk_df = pl.DataFrame(
        [
            ("D+698", 698),
            ("E+1456", 101456),
            ("F+230", 200230),
            ("G+125", 300125),
            ("H+456", 400456),
        ],
        orient="row",
        schema=["pk_ext", "pk_int"],
    ).with_columns(
        pk.ext_to_int(pl.col("pk_ext")).alias("pk_int2"),
    )
    assert pk_df["pk_int"].equals(pk_df["pk_int2"])


def test_m_to_int_ext():
    pk_df = pl.DataFrame(
        [
            (-214, -214, "0-214"),
            (456, 456, "0+456"),
            (100000, 1000, "1+000"),
            (100373, 1373, "1+373"),
            (7400388, 74388, "74+388"),
            (23400251, 234251, "234+251"),
            (41300000, 413000, "413+000"),
        ],
        orient="row",
        schema=["pk_int", "pk_m", "pk_ext"],
    ).with_columns(
        pk.m_to_int(pl.col("pk_m")).alias("pk_int2"), pk.m_to_ext(pl.col("pk_m")).alias("pk_ext2")
    )
    assert pk_df["pk_int"].equals(pk_df["pk_int2"])
    assert pk_df["pk_ext"].equals(pk_df["pk_ext2"])


def test_rk_dm_to_ext():
    df = pl.DataFrame(
        [
            ("123", 62.0, "123+062"),
            ("0", -6, "0-006"),
            ("12", 1054, "12+1054"),
            ("12B", 1054, "12B+1054"),
        ],
        orient="row",
        schema=["rk", "dm", "pk_ext"],
    )
    df2 = df.with_columns(pk.rk_dm_to_ext(pl.col("rk"), pl.col("dm")).alias("pk_ext2"))
    assert df2["pk_ext2"].equals(df2["pk_ext"])


def test_rk_dm_to_int():
    df = pl.DataFrame(
        [
            ("123", 62.0, 12300062),
            ("0", -6, -6),
            ("12", 1054, 1201054),
            ("12B", 1054, 1211054),
        ],
        orient="row",
        schema=["rk", "dm", "pk_int"],
    )
    df2 = df.with_columns(pk.rk_dm_to_int(pl.col("rk"), pl.col("dm")).alias("pk_int2"))
    assert df2["pk_int2"].equals(df2["pk_int"])
