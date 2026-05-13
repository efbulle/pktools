"""Module de conversion entre représentations des pk."""

import polars as pl

REGEX_PK_EXT = r"(?P<add1>\d{1,3}|[DEFGH])(?P<comp>[BTQ]?)(?P<op>[+-])(?P<add2>\d{3,4})"
# pk particuliers pour lignes 983000 et 984000 (Invalides à Austerlitz)
RER_C = {"D": "0", "E": "1", "F": "2", "G": "3", "H": "4"}
COMP_MAP = {"": 0, "B": 1, "T": 2, "Q": 3}
OP_MAP = {"+": 1, "-": -1}


def _int_to_m_and_ext(pk: pl.Expr) -> tuple[pl.Expr, pl.Expr]:
    """Décomposer un pk interne en composantes et le convertir.

    Conversion en pk métriques (pk_m) et pk extérieurs (pk_ext).
    Pour la conversion en pk_m, l'information du complément ou des milliers est perdue.

    Args:
        pk_internes: expression représentant une série d'entiers

    Returns:
        pk_m, pk_ext: expressions pour séries d'entiers et de chaînes
    """
    dizmil = pk.abs() // 10000
    milliersb = pk.abs() % 10000
    milliers_raw = milliersb // 1000
    centaines_raw = milliersb % 1000
    rk = dizmil // 10
    repere = dizmil % 10
    milliers = pl.when(pk > 0).then(milliers_raw).otherwise(-milliers_raw)
    centaines = pl.when(pk > 0).then(centaines_raw).otherwise(-centaines_raw)
    pk_m = ((centaines + (milliers + repere) * 1000) + rk * 1000).cast(pl.Int64)
    pk_ext = (
        rk.cast(pl.String)
        + repere.replace_strict({0: "", 1: "B", 2: "T", 3: "Q"}, return_dtype=pl.String)
        + pl.when(centaines >= 0).then(pl.lit("+")).otherwise(pl.lit("-"))
        + (milliers.abs() * 1000 + centaines.abs()).cast(pl.String).str.pad_start(3, "0")
    )
    return pk_m, pk_ext


def int_to_m(pk_internes: pl.Expr) -> pl.Expr:
    """Convertir une expression de pk internes en pk métriques."""
    return _int_to_m_and_ext(pk_internes)[0]


def int_to_ext(pk_internes: pl.Expr) -> pl.Expr:
    """Convertir une expression de pk internes en pk extérieurs."""
    return _int_to_m_and_ext(pk_internes)[1]


def ext_to_int(pk_ext: pl.Expr) -> pl.Expr:
    """Convertir une expression de pk externes en pk internes."""
    groups = pk_ext.str.extract_groups(REGEX_PK_EXT)
    # le cas courant est que add1 soit numérique mais il y a des exceptions sur le RER C
    add1 = groups.struct.field("add1").replace(RER_C).cast(pl.Int64)
    comp = groups.struct.field("comp").replace_strict(COMP_MAP)
    op = groups.struct.field("op").replace_strict(OP_MAP)
    add2 = groups.struct.field("add2").cast(pl.Int64)
    return (add1 * 100000 + comp * 10000 + op * add2).name.keep()


def m_to_int(pk_m: pl.Expr) -> pl.Expr:
    """Convertir une expression de pk métriques en pk internes."""
    abs_pk = pk_m.abs()
    milliers = abs_pk.floordiv(1000)
    centaines = abs_pk.mod(1000)
    pk_int = milliers * 100000 + centaines
    return pl.when(pk_m >= 0).then(pk_int).otherwise(pk_m)


def ext_to_m(pk_ext: pl.Expr) -> pl.Expr:
    """Convertir une expression de pk externes en pk métriques."""
    return int_to_m(ext_to_int(pk_ext))


def m_to_ext(pk_m: pl.Expr) -> pl.Expr:
    """Convertir une expression de pk métriques en pk externes."""
    return int_to_ext(m_to_int(pk_m))


def rk_dm_to_ext(rk: pl.Expr, dm: pl.Expr) -> pl.Expr:
    """Convertir des pk internes (base + ajout) en pk externes."""
    op = pl.when(dm >= 0).then(pl.lit("+")).otherwise(pl.lit("-"))
    return pl.format("{}{}{}", rk, op, dm.abs().cast(pl.Int32).cast(pl.String).str.zfill(3))
