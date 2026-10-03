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


class TestZHEdgeCases:
    """Cas extrêmes pour zones_homogenes : chevauchements, doublons et valeurs manquantes."""

    def test_overlap_within_single_df(self):
        """Deux intervalles qui se chevauchent dans un même DataFrame.

        La zone de chevauchement est couverte par les deux intervalles source :
        elle apparaît donc deux fois dans le résultat (une fois par intervalle
        source qui la couvre).
        """
        df = pl.DataFrame([(1, 0, 10), (1, 5, 20)], orient="row", schema=["lig", "pkmd", "pkmf"])
        res = pk.zones_homogenes([df], on="lig", pk_lbls=("pkmd", "pkmf"))
        expected = pl.DataFrame(
            [(1, 0, 5), (1, 5, 10), (1, 5, 10), (1, 10, 20)],
            orient="row",
            schema=["lig", "pkmd", "pkmf"],
        )
        assert res.sort("lig", "pkmd", "pkmf").equals(expected.sort("lig", "pkmd", "pkmf"))

    def test_overlap_across_two_dfs(self):
        """Chevauchement entre intervalles provenant de deux DataFrames distincts.

        La zone commune aux deux intervalles chevauchants est renseignée par
        les deux tables (ni id1 ni id2 n'est nul sur cette zone).
        """
        df1 = pl.DataFrame([(1, 0, 10)], orient="row", schema=["lig", "pkmd", "pkmf"])
        df2 = pl.DataFrame([(1, 5, 15)], orient="row", schema=["lig", "pkmd", "pkmf"])
        res = pk.zones_homogenes([df1, df2], on="lig", pk_lbls=("pkmd", "pkmf"))
        assert res.sort("pkmd").select("lig", "pkmd", "pkmf").to_dicts() == [
            {"lig": 1, "pkmd": 0, "pkmf": 5},
            {"lig": 1, "pkmd": 5, "pkmf": 10},
            {"lig": 1, "pkmd": 10, "pkmf": 15},
        ]

    def test_duplicate_rows_within_single_df(self):
        """Deux lignes strictement identiques (mêmes bornes) dans un même DataFrame.

        Chaque ligne source produit sa propre ligne de sortie : le résultat
        contient donc deux lignes identiques (une par doublon).
        """
        df = pl.DataFrame([(1, 0, 10), (1, 0, 10)], orient="row", schema=["lig", "pkmd", "pkmf"])
        res = pk.zones_homogenes([df], on="lig", pk_lbls=("pkmd", "pkmf"))
        assert res.height == 2
        assert res.select("lig", "pkmd", "pkmf").to_dicts() == [
            {"lig": 1, "pkmd": 0, "pkmf": 10},
            {"lig": 1, "pkmd": 0, "pkmf": 10},
        ]

    def test_duplicate_rows_across_multiple_dfs(self):
        """Un même intervalle dupliqué deux fois dans une table, croisé avec
        une autre table qui ne le contient qu'une fois.

        Le produit croisé des lignes correspondantes est bien matérialisé :
        une ligne de sortie par combinaison source/doublon.
        """
        df1 = pl.DataFrame({"lig": [1, 1], "pkmd": [0, 0], "pkmf": [10, 10], "v1": [10, 20]})
        df2 = pl.DataFrame({"lig": [1], "pkmd": [0], "pkmf": [10], "v2": ["x"]})
        res = pk.zones_homogenes([df1, df2], on="lig", pk_lbls=("pkmd", "pkmf"))
        assert res.sort("v1").to_dicts() == [
            {"lig": 1, "pkmd": 0, "pkmf": 10, "v1": 10, "v2": "x"},
            {"lig": 1, "pkmd": 0, "pkmf": 10, "v1": 20, "v2": "x"},
        ]

    def test_duplicate_whole_dataframe(self):
        """Un même DataFrame fourni deux fois dans ``df_list``.

        Les zones ne sont pas dupliquées car chaque intervalle source
        correspond exactement à une unique zone (pas de collision multiple).
        """
        df = pl.DataFrame([(1, 0, 10), (1, 10, 20)], orient="row", schema=["lig", "pkmd", "pkmf"])
        res = pk.zones_homogenes([df, df.clone()], on="lig", pk_lbls=("pkmd", "pkmf"))
        assert (
            res.sort("pkmd")
            .select("lig", "pkmd", "pkmf")
            .equals(df.sort("pkmd").select("lig", "pkmd", "pkmf"))
        )

    def test_group_missing_from_one_table(self):
        """Groupe (valeur de ``on``) présent dans une table mais absent d'une autre.

        Les zones issues du groupe non partagé sont tout de même incluses,
        puisqu'elles sont couvertes par au moins un DataFrame.
        """
        df1 = pl.DataFrame([(1, 0, 10), (2, 0, 10)], orient="row", schema=["lig", "pkmd", "pkmf"])
        df2 = pl.DataFrame([(1, 0, 10)], orient="row", schema=["lig", "pkmd", "pkmf"])
        res = pk.zones_homogenes([df1, df2], on="lig", pk_lbls=("pkmd", "pkmf"))
        assert res.sort("lig").select("lig", "pkmd", "pkmf").to_dicts() == [
            {"lig": 1, "pkmd": 0, "pkmf": 10},
            {"lig": 2, "pkmd": 0, "pkmf": 10},
        ]

    def test_group_missing_from_all_but_one_table(self):
        """Groupe présent dans une seule table parmi trois.

        Les colonnes d'identifiant des tables qui ne couvrent pas le groupe
        valent null pour les zones correspondantes.
        """
        df1 = pl.DataFrame([(1, 0, 10)], orient="row", schema=["lig", "pkmd", "pkmf"]).with_columns(
            id1=pl.row_index()
        )
        df2 = pl.DataFrame([(2, 0, 10)], orient="row", schema=["lig", "pkmd", "pkmf"]).with_columns(
            id2=pl.row_index()
        )
        df3 = pl.DataFrame([(3, 0, 10)], orient="row", schema=["lig", "pkmd", "pkmf"]).with_columns(
            id3=pl.row_index()
        )
        res = pk.zones_homogenes([df1, df2, df3], on="lig", pk_lbls=("pkmd", "pkmf"))
        assert res.sort("lig").to_dicts() == [
            {"lig": 1, "pkmd": 0, "pkmf": 10, "id1": 0, "id2": None, "id3": None},
            {"lig": 2, "pkmd": 0, "pkmf": 10, "id1": None, "id2": 0, "id3": None},
            {"lig": 3, "pkmd": 0, "pkmf": 10, "id1": None, "id2": None, "id3": 0},
        ]

    def test_null_value_in_grouping_column(self):
        """Valeur nulle dans la colonne de regroupement ``on``.

        La ligne dont la valeur de ``on`` est nulle n'est rattachée à aucun
        groupe valide et n'apparaît donc pas dans le résultat.
        """
        df = pl.DataFrame({"lig": [1, None], "pkmd": [0, 0], "pkmf": [10, 10]})
        res = pk.zones_homogenes([df], on="lig", pk_lbls=("pkmd", "pkmf"))
        assert res.to_dicts() == [{"lig": 1, "pkmd": 0, "pkmf": 10}]

    def test_null_value_in_payload_column(self):
        """Valeur nulle dans une colonne qui n'est ni clé de regroupement ni borne de PK.

        La valeur nulle est simplement propagée dans le résultat.
        """
        df = pl.DataFrame({"lig": [1, 1], "pkmd": [0, 10], "pkmf": [10, 20], "cat": [None, "b"]})
        res = pk.zones_homogenes([df], on="lig", pk_lbls=("pkmd", "pkmf"))
        assert res.sort("pkmd").to_dicts() == [
            {"lig": 1, "pkmd": 0, "pkmf": 10, "cat": None},
            {"lig": 1, "pkmd": 10, "pkmf": 20, "cat": "b"},
        ]

    def test_multiple_on_columns(self):
        """Regroupement sur plusieurs colonnes simultanément."""
        df1 = pl.DataFrame({"lig": [1, 1], "voie": ["V1", "V2"], "pkmd": [0, 0], "pkmf": [10, 10]})
        df2 = pl.DataFrame({"lig": [1], "voie": ["V1"], "pkmd": [5], "pkmf": [15]})
        res = pk.zones_homogenes([df1, df2], on=["lig", "voie"], pk_lbls=("pkmd", "pkmf"))
        assert res.sort("voie", "pkmd").select("lig", "voie", "pkmd", "pkmf").to_dicts() == [
            {"lig": 1, "voie": "V1", "pkmd": 0, "pkmf": 5},
            {"lig": 1, "voie": "V1", "pkmd": 5, "pkmf": 10},
            {"lig": 1, "voie": "V1", "pkmd": 10, "pkmf": 15},
            {"lig": 1, "voie": "V2", "pkmd": 0, "pkmf": 10},
        ]

    def test_empty_df_list_mix(self):
        """Une table vide (0 ligne) mêlée à une table non vide.

        Aucune zone n'est générée à partir de la table vide, mais le résultat
        reste correct pour les autres tables.
        """
        df1 = pl.DataFrame([(1, 0, 10)], orient="row", schema=["lig", "pkmd", "pkmf"])
        df2 = pl.DataFrame(schema={"lig": pl.Int64, "pkmd": pl.Int64, "pkmf": pl.Int64})
        res = pk.zones_homogenes([df1, df2], on="lig", pk_lbls=("pkmd", "pkmf"))
        assert res.select("lig", "pkmd", "pkmf").to_dicts() == [{"lig": 1, "pkmd": 0, "pkmf": 10}]


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
