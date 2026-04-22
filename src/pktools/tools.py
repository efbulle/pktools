"""Module de manipulation des tronçons."""

import polars as pl
import polars.selectors as cs


def zones_homogenes(
    df_list: list[pl.DataFrame],
    on: str | list[str],
    pk_lbls: tuple[str, str] = ("pk_int_d", "pk_int_f"),
    id_prefix: str = "_id",
    df_suffix: str = "_df",
):
    """Calcule les zones homogènes par jointure d'intervalles sur plusieurs DataFrames.

    Construit une grille de PK à partir de l'union de tous les points de rupture
    présents dans ``df_list``, puis joint chaque DataFrame sur cette grille de façon
    à ce que chaque ligne du résultat corresponde à un tronçon élémentaire couvert
    par au moins un des DataFrames d'entrée.

    Parameters
    ----------
    df_list :
        Liste de DataFrames à joindre. Chacun doit contenir les colonnes ``on``
        ainsi que les deux colonnes de PK définies par ``pk_lbls``.
    on :
        Colonne(s) de regroupement (clé(s) de jointure hors PK).
    pk_lbls :
        Noms des colonnes de début et fin d'intervalle (dans cet ordre).
    id_prefix :
        Préfixe utilisé pour les colonnes d'index de ligne internes.
        Ne doit pas coïncider avec un préfixe de colonne existant.
    df_suffix :
        Suffixe utilisé pour disambiguïser les colonnes en collision entre DataFrames.
        Ne doit pas coïncider avec un suffixe de colonne existant.

    Returns
    -------
    pl.DataFrame
        DataFrame dont chaque ligne est un tronçon élémentaire, avec les colonnes
        de tous les DataFrames d'entrée (suffixées en cas de collision de noms).
        Les tronçons non couverts par au moins un DataFrame sont exclus.
    """
    from collections import Counter

    pkd, pkf = pk_lbls
    if isinstance(on, str):
        on = [on]

    # --- Phase 1: build the PK grid (eager, needs shift().over()) ---
    all_pks = []
    for df in df_list:
        all_pks.append(
            df.select(on + list(pk_lbls)).unpivot(index=on, value_name="pk").drop("variable")
        )

    loc = (
        pl.concat(all_pks)
        .unique()
        .sort(on + ["pk"])
        .with_columns(pl.col("pk").shift(-1).over(on).alias(pkf))
        .filter(pl.col(pkf).is_not_null())
        .rename({"pk": pkd})
    )

    # --- Detect collisions across all dataframes ---
    all_payload_cols = [c for df in df_list for c in df.columns if c not in on + list(pk_lbls)]
    collision_cols = {c for c, n in Counter(all_payload_cols).items() if n > 1}

    # --- Phase 2: lazy joins per df ---
    loc_lazy = loc.lazy()
    final_lazy = loc_lazy

    for i, df in enumerate(df_list):
        row_idx = f"{id_prefix}{i}"
        pkd_ref = f"{pkd}{df_suffix}{i}"
        pkf_ref = f"{pkf}{df_suffix}{i}"
        df_with_idx = df.with_row_index(row_idx)
        df_lazy = df_with_idx.lazy().rename({pkd: pkd_ref, pkf: pkf_ref})

        zone_match = (
            loc_lazy.join(df_lazy.select(on + [row_idx, pkd_ref, pkf_ref]), on=on, how="left")
            .filter(
                pl.col(pkd_ref).is_null()
                | ((pl.col(pkd_ref) <= pl.col(pkd)) & (pl.col(pkf) <= pl.col(pkf_ref)))
            )
            .select(on + [pkd, pkf, row_idx])
        )
        payload_cols = [
            pl.col(c).alias(f"{c}{df_suffix}{i}") if c in collision_cols else pl.col(c)
            for c in df.columns
            if c not in on + list(pk_lbls)
        ]
        payload = df_with_idx.lazy().select(row_idx, *payload_cols)

        final_lazy = final_lazy.join(zone_match, on=on + [pkd, pkf], how="left").join(
            payload, on=row_idx, how="left"
        )

    return (
        final_lazy.filter(pl.any_horizontal(cs.starts_with(id_prefix).is_not_null()))
        .drop(cs.starts_with(id_prefix))
        .collect(engine="streaming")
    )


def calcule_cc(
    df: pl.DataFrame, by: str | list[str], pk_lbls: tuple[str, str] = ("pk_int_d", "pk_int_f")
) -> pl.DataFrame:
    """Calcule les composantes connexes d'intervalles chevauchants.

    Fusionne les intervalles qui se chevauchent ou se touchent au sein de chaque
    groupe défini par ``by``, en retournant un intervalle englobant par composante.

    Parameters
    ----------
    df :
        DataFrame contenant les intervalles à fusionner.
    by :
        Colonne(s) de regroupement : la fusion n'est effectuée qu'au sein
        de chaque groupe.
    pk_lbls :
        Noms des colonnes de début et fin d'intervalle (dans cet ordre).

    Returns
    -------
    pl.DataFrame
        DataFrame avec les mêmes colonnes que l'entrée, où chaque ligne représente
        une composante connexe (intervalle fusionné). L'ordre des lignes n'est pas
        garanti.

    Notes
    -----
    Deux intervalles ``[a, b]`` et ``[c, d]`` sont considérés comme connexes
    si ``c <= b`` (contact inclus). Les intervalles purement adjacents
    (``c == b``) sont donc fusionnés.
    """
    start, end = pk_lbls
    if isinstance(by, str):
        by = [by]

    return (
        df.sort(by + [start])
        .with_columns([pl.col(end).cum_max().over(by).alias("running_max_end")])
        .with_columns(
            (
                pl.when(pl.col(start) > pl.col("running_max_end").shift().over(by))
                .then(1)
                .otherwise(0)
            ).alias("new_group")
        )
        .with_columns(pl.cum_sum("new_group").over(by).alias("group_id"))
        .group_by(by + ["group_id"], maintain_order=True)
        .agg(
            [
                pl.col(start).min().alias(start),
                pl.col(end).max().alias(end),
            ]
        )
        .drop("group_id")
    )


def self_intersect(
    df: pl.DataFrame, on: str | list[str], pk_lbls: tuple[str, str] = ("pk_int_d", "pk_int_f")
) -> pl.DataFrame:
    """Détecte les paires d'intervalles qui se chevauchent au sein d'un même groupe.

    Effectue une auto-jointure sur les colonnes ``on`` et filtre les paires dont
    les intervalles ont une intersection strictement positive (les contacts exacts
    sont exclus).

    Parameters
    ----------
    df :
        DataFrame contenant les intervalles à examiner.
    on :
        Colonne(s) de regroupement : seuls les intervalles d'un même groupe
        sont comparés entre eux.
    pk_lbls :
        Noms des colonnes de début et fin d'intervalle (dans cet ordre).

    Returns
    -------
    pl.DataFrame
        DataFrame issu de l'auto-jointure, contenant les paires d'intervalles
        en chevauchement (une ligne par paire non ordonnée). La colonne ``_lg``
        indique la longueur du chevauchement.

    Notes
    -----
    Seules les paires non ordonnées sont retournées (``id < id_right``),
    ce qui évite les doublons. Les chevauchements de longueur nulle
    (contact exact) sont exclus.
    """
    pkd, pkf = pk_lbls
    df_idx = df.with_row_index("id")
    return (
        df_idx.join(df_idx, on=on, how="inner")
        .filter(
            (pl.col("id") < pl.col("id_right"))
            & (pl.col(pkd) <= pl.col(pkf + "_right"))
            & (pl.col(pkf) >= pl.col(pkd + "_right"))
        )
        .with_columns(
            _lg=pl.min_horizontal(pkf, pkf + "_right") - pl.max_horizontal(pkd, pkd + "_right")
        )
        .filter(pl.col("_lg") > 0)
    )
