import polars as pl
import pytest

import pktools as pk


class TestZH:
    @pytest.fixture(autouse=True)
    def setup_vars(self):
        self.df1 = pl.DataFrame(
            [
                (1, 0, 10),
                (1, 10, 20),
                (1, 20, 100),
                (2, 10, 50),
                (2, 50, 300),
                (3, 0, 100),
                (4, 50, 70),
            ],
            orient="row",
            schema=["lig", "pkmd", "pkmf"],
        ).with_columns(id1=pl.row_index())
        self.df2 = pl.DataFrame(
            [
                (1, 0, 80),
                (1, 80, 120),
                (2, 0, 500),
                (3, 30, 70),
                (3, 70, 130),
                (5, 20, 80),
            ],
            orient="row",
            schema=["lig", "pkmd", "pkmf"],
        ).with_columns(id2=pl.row_index())
        self.df3 = pl.DataFrame(
            [
                (2, 0, 50),
                (2, 50, 400),
                (3, 0, 100),
                (4, 50, 80),
                (6, 30, 900),
            ],
            orient="row",
            schema=["lig", "pkmd", "pkmf"],
        ).with_columns(id3=pl.row_index())

    def test_zh_single(self):
        res = pk.zones_homogenes([self.df1], on="lig", pk_lbls=("pkmd", "pkmf"))
        assert res.sort("lig", "pkmd").equals(self.df1.sort("lig", "pkmd"))

    def test_zh_chunks(self):
        res = pk.zones_homogenes([self.df1, self.df2], on="lig", pk_lbls=("pkmd", "pkmf"))
        expected = pl.DataFrame(
            {
                "lig": [1, 1, 1, 1, 1, 2, 2, 2, 2, 3, 3, 3, 3, 4, 5],
                "pkmd": [0, 10, 20, 80, 100, 0, 10, 50, 300, 0, 30, 70, 100, 50, 20],
                "pkmf": [10, 20, 80, 100, 120, 10, 50, 300, 500, 30, 70, 100, 130, 70, 80],
                "id1": [0, 1, 2, 2, None, None, 3, 4, None, 5, 5, 5, None, 6, None],
                "id2": [0, 0, 0, 1, 1, 2, 2, 2, 2, None, 3, 4, 4, None, 5],
            }
        )
        assert res.sort("lig", "pkmd").equals(expected.sort("lig", "pkmd"))

    def test_zh3(self):
        res = pk.zones_homogenes([self.df1, self.df2, self.df3], on="lig", pk_lbls=("pkmd", "pkmf"))
        expected = pl.DataFrame(
            {
                "lig": [1, 1, 1, 1, 1, 2, 2, 2, 2, 2, 3, 3, 3, 3, 4, 4, 5, 6],
                "pkmd": [
                    0,
                    10,
                    20,
                    80,
                    100,
                    0,
                    10,
                    50,
                    300,
                    400,
                    0,
                    30,
                    70,
                    100,
                    50,
                    70,
                    20,
                    30,
                ],
                "pkmf": [
                    10,
                    20,
                    80,
                    100,
                    120,
                    10,
                    50,
                    300,
                    400,
                    500,
                    30,
                    70,
                    100,
                    130,
                    70,
                    80,
                    80,
                    900,
                ],
                "id1": [
                    0,
                    1,
                    2,
                    2,
                    None,
                    None,
                    3,
                    4,
                    None,
                    None,
                    5,
                    5,
                    5,
                    None,
                    6,
                    None,
                    None,
                    None,
                ],
                "id2": [
                    0,
                    0,
                    0,
                    1,
                    1,
                    2,
                    2,
                    2,
                    2,
                    2,
                    None,
                    3,
                    4,
                    4,
                    None,
                    None,
                    5,
                    None,
                ],
                "id3": [
                    None,
                    None,
                    None,
                    None,
                    None,
                    0,
                    0,
                    1,
                    1,
                    None,
                    2,
                    2,
                    2,
                    None,
                    3,
                    3,
                    None,
                    4,
                ],
            }
        )
        assert res.sort("lig", "pkmd").equals(expected.sort("lig", "pkmd"))

    def test_zh_disjointes(self):
        df = pl.DataFrame(
            [
                (1, 0, 50),
                (1, 100, 400),
                (2, 0, 100),
            ],
            orient="row",
            schema=["lig", "pkmd", "pkmf"],
        )
        res = pk.zones_homogenes([df], on="lig", pk_lbls=("pkmd", "pkmf"))
        assert res.sort("lig", "pkmd").equals(df.sort("lig", "pkmd"))

    def test_zh_collision_cols(self):
        df = pl.DataFrame(
            [
                (1, 0, 50),
                (1, 100, 400),
                (2, 0, 100),
            ],
            orient="row",
            schema=["lig", "pkmd", "pkmf"],
        ).with_columns(a=1)
        df2 = pl.DataFrame(
            [
                (1, 0, 20),
                (1, 50, 120),
                (2, 50, 150),
            ],
            orient="row",
            schema=["lig", "pkmd", "pkmf"],
        ).with_columns(a=2, b=1)
        res = pk.zones_homogenes([df, df2], on="lig", pk_lbls=("pkmd", "pkmf"))
        assert res.columns == ["lig", "pkmd", "pkmf", "a_df0", "a_df1", "b"]


class TestCC:
    def test_overlapping_intervals(self):
        """Test merging of overlapping intervals."""
        df = pl.DataFrame(
            {"lig": ["A", "A", "A"], "pk_int_d": [1, 8, 20], "pk_int_f": [10, 15, 25]}
        )
        expected = pl.DataFrame({"lig": ["A", "A"], "pk_int_d": [1, 20], "pk_int_f": [15, 25]})
        result = pk.calcule_cc(df, by="lig")
        assert result.equals(expected)

    def test_adjacent_intervals(self):
        """Test intervals that touch but don't overlap."""
        df = pl.DataFrame({"lig": ["A", "A"], "pk_int_d": [1, 11], "pk_int_f": [10, 20]})
        expected = pl.DataFrame({"lig": ["A", "A"], "pk_int_d": [1, 11], "pk_int_f": [10, 20]})
        result = pk.calcule_cc(df, by="lig")
        assert result.equals(expected)

    def test_multiple_groups(self):
        """Test handling multiple groups independently."""
        df = pl.DataFrame(
            {
                "lig": ["A", "A", "B", "B"],
                "pk_int_d": [1, 5, 100, 105],
                "pk_int_f": [10, 15, 110, 115],
            }
        )
        expected = pl.DataFrame({"lig": ["A", "B"], "pk_int_d": [1, 100], "pk_int_f": [15, 115]})
        result = pk.calcule_cc(df, by="lig")
        assert result.equals(expected)

    def test_overlap_before_previous(self):
        """Test handling of overlap with distant rows."""
        df = pl.DataFrame(
            {
                "lig": ["A", "A", "A", "A", "A", "B", "B"],
                "pk_int_d": [1, 1, 5, 8, 20, 100, 105],
                "pk_int_f": [10, 15, 7, 10, 30, 110, 115],
            }
        )
        expected = pl.DataFrame(
            {"lig": ["A", "A", "B"], "pk_int_d": [1, 20, 100], "pk_int_f": [15, 30, 115]}
        )
        result = pk.calcule_cc(df, by="lig")
        assert result.equals(expected)

    def test_no_overlap(self):
        """Test intervals with gaps (no merging needed)."""
        df = pl.DataFrame({"lig": ["A", "A"], "pk_int_d": [1, 20], "pk_int_f": [10, 30]})
        expected = pl.DataFrame({"lig": ["A", "A"], "pk_int_d": [1, 20], "pk_int_f": [10, 30]})
        result = pk.calcule_cc(df, by="lig")
        assert result.equals(expected)

    def test_single_interval(self):
        """Test single interval (edge case)."""
        df = pl.DataFrame({"lig": ["A"], "pk_int_d": [1], "pk_int_f": [10]})
        expected = pl.DataFrame({"lig": ["A"], "pk_int_d": [1], "pk_int_f": [10]})
        result = pk.calcule_cc(df, by="lig")
        assert result.equals(expected)

    def test_custom_column_names(self):
        """Test with custom column names."""
        df = pl.DataFrame({"id": ["X"], "start_date": [1], "end_date": [10]})
        expected = pl.DataFrame({"id": ["X"], "start_date": [1], "end_date": [10]})
        result = pk.calcule_cc(df, by=["id"], pk_lbls=("start_date", "end_date"))
        assert result.equals(expected)

    def test_complete_overlap(self):
        """Test when one interval completely contains another."""
        df = pl.DataFrame({"lig": ["A", "A"], "pk_int_d": [1, 5], "pk_int_f": [20, 10]})
        expected = pl.DataFrame({"lig": ["A"], "pk_int_d": [1], "pk_int_f": [20]})
        result = pk.calcule_cc(df, by="lig")
        assert result.equals(expected)

    def test_by_is_none(self):
        df = pl.DataFrame({"lig": ["A", "A", "A"], "pkd": [1, 8, 20], "pkf": [10, 15, 25]})
        expected = pl.DataFrame({"lig": ["A", "A"], "pkd": [1, 20], "pkf": [15, 25]})
        result = pk.calcule_cc(df, pk_lbls=("pkd", "pkf"))
        assert result.equals(expected)


class TestSelfIntersect:
    """Test cases for the self_intersect function."""

    def test_no_overlaps(self):
        """Test with non-overlapping intervals - should return empty DataFrame."""
        df = pl.DataFrame(
            {
                "lig": ["A", "A", "A"],
                "pk_int_d": [0, 10, 20],
                "pk_int_f": [5, 15, 25],
            }
        )
        result = pk.self_intersect(df, on="lig")
        assert result.height == 0

    def test_simple_overlap(self):
        """Test with two overlapping intervals."""
        df = pl.DataFrame({"lig": ["A", "A"], "pk_int_d": [0, 5], "pk_int_f": [10, 15]})
        result = pk.self_intersect(df, on="lig")
        assert result.height == 1
        assert result["_lg"][0] == 5  # Overlap from 5 to 10

    def test_multiple_overlaps(self):
        """Test with multiple overlapping pairs."""
        df = pl.DataFrame(
            {
                "lig": ["A", "A", "A"],
                "pk_int_d": [0, 5, 8],
                "pk_int_f": [10, 15, 20],
            }
        )
        result = pk.self_intersect(df, on="lig")
        assert result.height == 3  # (0,1), (0,2), (1,2) all overlap

    def test_adjacent_intervals_no_overlap(self):
        """Test adjacent intervals that touch but don't overlap."""
        df = pl.DataFrame({"lig": ["A", "A"], "pk_int_d": [0, 10], "pk_int_f": [10, 20]})
        result = pk.self_intersect(df, on="lig")
        assert result.height == 0  # Adjacent but _lg = 0, filtered out

    def test_complete_overlap(self):
        """Test interval completely contained within another."""
        df = pl.DataFrame({"lig": ["A", "A"], "pk_int_d": [0, 5], "pk_int_f": [20, 10]})
        result = pk.self_intersect(df, on="lig")
        assert result.height == 1
        assert result["_lg"][0] == 5  # Smaller interval length

    def test_different_groups_no_overlap(self):
        """Test that intervals in different groups don't match."""
        df = pl.DataFrame({"lig": ["A", "B"], "pk_int_d": [0, 5], "pk_int_f": [10, 15]})
        result = pk.self_intersect(df, on="lig")
        assert result.height == 0  # Different groups, no comparison

    def test_same_group_mixed_overlaps(self):
        """Test multiple groups with some overlaps."""
        df = pl.DataFrame(
            {
                "lig": ["A", "A", "B", "B"],
                "pk_int_d": [0, 5, 0, 10],
                "pk_int_f": [10, 15, 15, 20],
            }
        )
        result = pk.self_intersect(df, on="lig")
        assert result.height == 2  # One overlap in A, one in B

    def test_custom_column_names(self):
        """Test with custom start/end column names."""
        df = pl.DataFrame({"lig": ["A", "A"], "start": [0, 5], "end": [10, 15]})
        result = pk.self_intersect(df, on="lig", pk_lbls=("start", "end"))
        assert result.height == 1
        assert "_lg" in result.columns

    def test_preserves_additional_columns(self):
        """Test that additional columns are preserved in output."""
        df = pl.DataFrame(
            {
                "lig": ["A", "A"],
                "pk_int_d": [0, 5],
                "pk_int_f": [10, 15],
                "cat1": [50, 60],
                "cat2": [2, 3],
            }
        )
        result = pk.self_intersect(df, on="lig")
        assert result.height == 1
        assert "cat1" in result.columns
        assert "cat1_right" in result.columns
        assert "cat2" in result.columns
        assert "cat2_right" in result.columns

    def test_single_interval(self):
        """Test with only one interval - should return empty."""
        df = pl.DataFrame({"lig": ["A"], "pk_int_d": [0], "pk_int_f": [10]})
        result = pk.self_intersect(df, on="lig")
        assert result.height == 0

    def test_identical_intervals(self):
        """Test with identical intervals."""
        df = pl.DataFrame({"lig": ["A", "A"], "pk_int_d": [0, 0], "pk_int_f": [10, 10]})
        result = pk.self_intersect(df, on="lig")
        assert result.height == 1
        assert result["_lg"][0] == 10  # Complete overlap
