# pktools

[![CI](https://github.com/efbulle/pktools/actions/workflows/ci.yml/badge.svg)](https://github.com/efbulle/pktools/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENCE)
[![Python](https://img.shields.io/badge/python-3.12%20%7C%203.13%20%7C%203.14-blue.svg)](pyproject.toml)

Modules de manipulation de pk (points kilométriques) et de tronçons.

**pktools** est un paquet Python spécialisé dans la gestion des points kilométriques (PK), un système de référençage linéaire utilisé pour le réseau ferroviaire. Il fournit des outils pour convertir entre différentes représentations de PK et manipuler des ensembles de tronçons.

## Installation

### Prérequis

- Python ≥ 3.12.3

### Installer via pip

```bash
pip install "pktools[polars]"
```

Polars et pandas sont des dépendances optionnelles et indépendantes. Les
conversions pandas seules s'installent avec :

```bash
pip install "pktools[pandas]"
```

Pour utiliser les deux backends : `pip install "pktools[polars,pandas]"`.
`pip install pktools` installe le paquet sans aucun backend. Il reste
importable, mais chaque backend doit être installé avant d'utiliser ses
fonctions ; les fonctions Polars donnent un message d'erreur indiquant
`pktools[polars]` si Polars manque.

**Migration depuis les versions précédentes :** Polars était auparavant
installé par défaut. Pour retrouver les dépendances et conversions habituelles,
mettez à jour l'installation avec `pip install "pktools[polars]"`.

## Utilisation

### Conversions de points kilométriques

Le module `conv` propose des fonctions de conversion entre trois représentations de PK :

- **PK internes** : représentation numérique entière interne (ex: `41200795`)
- **PK externes** : représentation lisible externe (ex: `412+795`)
- **PK métriques** : distance en mètres depuis l'origine (ex: `412795`)

### Exemples rapides

```python
import polars as pl
import pktools as pk

df = pl.DataFrame(
    {
        "pk_ext": ["74+388", "412B+795", "0-214"],
    }
).with_columns(
    pk_int=pk.ext_to_int(pl.col("pk_ext")),
    pk_m=pk.ext_to_m(pl.col("pk_ext")),
)

print(df)
```

```python
import polars as pl
import pktools as pk

df = pl.DataFrame(
    {
        "pk_int": [7400388, 41210795, -214],
    }
).with_columns(
    pk_ext=pk.int_to_ext(pl.col("pk_int")),
    pk_m=pk.int_to_m(pl.col("pk_int")),
)

print(df)
```

### Notes de comportement

- Les conversions sont vectorisées pour des colonnes `polars.Expr`.
- Pour les chaînes de PK externes invalides, l'extraction échoue et produit des valeurs nulles.
- La conversion vers PK métrique est une représentation simplifiée: certaines informations de repère/complement ne sont pas conservées.

### Conversions pandas strictes

L'interface `pktools.pandas` ne requiert ni n'importe Polars. Installez
`pktools[pandas]`. Elle expose
`ext_to_int`, `ext_to_m`, `int_to_ext`, `int_to_m`, `m_to_int`, `m_to_ext`,
`rk_dm_to_ext` et `rk_dm_to_int`. Elle ne porte pas les fonctions de tronçons.

```python
import pandas as pd
from pktools import pandas as pk

pk_ext = pd.Series(["4+514", "412B+795", None], index=["a", "b", "c"], name="pk")
pk_m = pk.ext_to_m(pk_ext)  # 4514, 413795, <NA> ; même index et nom
```

- Chaque argument est une `pandas.Series` ; pour les fonctions à deux
  arguments, les index doivent être identiques, y compris leur ordre et leurs
  doublons. Les entrées sont validées indépendamment, même si l'autre valeur
  de la ligne est manquante.
- Les PK externes sont des chaînes entières, sans espaces ni sous-chaîne
  supplémentaire : 1 à 3 chiffres ASCII ou une lettre `D` à `H`, suivis
  éventuellement de `B`, `T` ou `Q`, puis de `+` ou `-` et de 3 ou 4 chiffres.
  Les lettres RER C correspondent à `D=0`, `E=1`, `F=2`, `G=3`, `H=4`.
  Les repères `rk` sont des chaînes suivant la même règle sans signe ni distance.
- Les PK numériques et distances `dm` sont des entiers ou flottants
  représentant exactement un entier (dans la limite de ±2⁵³ pour les
  flottants). Les booléens, chaînes numériques, fractions et infinis sont
  refusés. `dm` doit être compris entre -9999 et 9999. Les valeurs sont
  limitées à l'intervalle Int64 sûr ; pour `m_to_int`/`m_to_ext`, le maximum
  positif est 92 233 720 368 547 999 afin d'éviter un dépassement. La conversion
  d'un PK interne en externe exige en outre un chiffre de complément de 0 à 3.
- `None`, `NaN` et `pd.NA` sont propagés comme `pd.NA` ; pour deux arguments,
  une valeur manquante dans l'un des deux rend la sortie manquante. Les sorties
  numériques sont de type pandas nullable `Int64`, les sorties externes de
  type `string`. L'index et le nom de la première série sont conservés.
- Toute valeur non manquante invalide provoque une `ValueError` indiquant le
  nombre total d'erreurs et jusqu'à dix triplets (position, index, valeur).
  Les non-`Series` provoquent une `TypeError`.
- Les règles et signes reproduisent les calculs Polars, y compris leurs cas
  particuliers : par exemple `int_to_ext(-1000)` produit `0+1000`. Le passage
  en mètres fusionne certaines représentations (compléments et dépassements
  kilométriques). La conversion externe → interne perd aussi la lettre RER C
  et les zéros de tête ; les conversions inverses ne reconstituent pas
  nécessairement la représentation d'origine.

Les constantes de syntaxe et les tables métier sont partagées avec Polars ;
les calculs sont distincts et vectorisés dans chaque moteur, avec une
validation des types des valeurs objet côté pandas. Les tests comparent les
résultats sur les entrées valides communes.

#### PyScript / Pyodide

Le wheel pktools est en Python pur. Le template du builder
[`cartes_multicouches`](https://github.com/efbulle/cartes_multicouches) utilise
PyScript `2026.7.3` et précharge `micropip` et `pandas`. Une vérification
manuelle dans ce runtime a installé le wheel avec l'installation normale de
`micropip` depuis `emfs://` (sans `deps=False`) : Python `3.14.2`, Pyodide
`314.0.3`, pandas `3.0.2`. Elle a confirmé `4+514` → `4514`, le rejet d'une
chaîne invalide et l'absence de Polars.

Ce contrôle ciblait l'installation du wheel et l'interface pandas dans le
runtime du navigateur, pas la génération ni l'exécution complète du HTML du
builder. Le wheel de base ne demande aucun paquet ; l'installation de l'extra
`pandas` via PyPI reste soumise à la disponibilité de wheels compatibles avec
la version de Pyodide concernée.

### Manipulation de tronçons

Le module `tools` propose des fonctions pour travailler avec des ensembles
d'intervalles (tronçons) définis par des colonnes de PK de début/fin :

- **`zones_homogenes`** : calcule les zones homogènes obtenues par jointure
  d'intervalles entre plusieurs `DataFrame`, en découpant sur l'union de tous
  les points de rupture.
- **`calcule_cc`** : fusionne les intervalles chevauchants ou adjacents au sein
  de chaque groupe (composantes connexes).
- **`self_intersect`** : détecte les paires d'intervalles qui se chevauchent
  au sein d'un même groupe.

Voir les docstrings de chaque fonction (format NumPy) pour le détail des
paramètres et des exemples.

#### `zones_homogenes`

`zones_homogenes` prend en entrée plusieurs `DataFrame` décrivant chacun un
découpage en tronçons (bornes de PK de début/fin) pour un même ensemble de
groupes (ex: une ligne ferroviaire). Elle recalcule un découpage commun en
« zones homogènes » : chaque zone de sortie est un tronçon élémentaire sur
lequel aucune des tables d'entrée ne change de valeur, avec les colonnes de
chaque table rattachées (suffixées en cas de collision de noms).

```python
import polars as pl
import pktools as pk

vitesse = pl.DataFrame(
    {
        "lig": [1, 1],
        "pk_int_d": [0, 500],
        "pk_int_f": [500, 1000],
        "vmax": [160, 220],
    }
)
travaux = pl.DataFrame(
    {
        "lig": [1],
        "pk_int_d": [300],
        "pk_int_f": [700],
        "ralenti": [True],
    }
)

zones = pk.zones_homogenes([vitesse, travaux], on="lig")
print(zones)
```

```text
shape: (3, 5)
┌─────┬──────────┬──────────┬──────┬─────────┐
│ lig ┆ pk_int_d ┆ pk_int_f ┆ vmax ┆ ralenti │
│ --- ┆ ---      ┆ ---      ┆ ---  ┆ ---     │
│ i64 ┆ i64      ┆ i64      ┆ i64  ┆ bool    │
╞═════╪══════════╪══════════╪══════╪═════════╡
│ 1   ┆ 0        ┆ 300      ┆ 160  ┆ null    │
│ 1   ┆ 300      ┆ 500      ┆ 160  ┆ true    │
│ 1   ┆ 500      ┆ 700      ┆ 220  ┆ true    │
│ 1   ┆ 700      ┆ 1000     ┆ 220  ┆ null    │
└─────┴──────────┴──────────┴──────┴─────────┘
```

**Cas d'usage et cas limites :**

- **Groupes absents d'une table** : si un groupe (valeur de `on`) n'existe
  que dans certaines tables, les zones correspondantes sont tout de même
  produites ; les colonnes issues des tables qui ne couvrent pas ce groupe
  valent `null`.
- **Intervalles chevauchants** : si deux intervalles d'une même table (ou
  de tables différentes) se chevauchent, la zone commune est rattachée aux
  deux intervalles sources ; une zone peut donc apparaître plusieurs fois
  dans le résultat si elle est couverte par plusieurs lignes d'une même table.
- **Lignes dupliquées** : des lignes strictement identiques (mêmes bornes,
  dans une ou plusieurs tables) produisent un produit croisé — chaque
  combinaison de lignes sources correspondantes donne lieu à une ligne de
  sortie distincte.
- **Valeurs manquantes** : une valeur nulle dans une colonne de charge utile
  (ni clé de regroupement, ni borne de PK) est simplement propagée. Une
  valeur nulle dans une colonne de regroupement (`on`) exclut la ligne
  correspondante du résultat, car elle ne peut être rattachée à aucun groupe.
- **Collisions de noms de colonnes** : si plusieurs tables partagent un nom
  de colonne (hors `on` et `pk_lbls`), les colonnes en conflit sont
  suffixées avec `df_suffix` (ex: `vmax_df0`, `vmax_df1`).

Voir les tests de `tests/test_tools.py::TestZHEdgeCases` pour des exemples
exécutables de ces cas limites.

## Dépendances

- **polars** (≥2.1.0) : extra `polars`, moteur des fonctions existantes.
- **pandas** (≥2.2) : extra `pandas`, indépendant de l'extra Polars.

## Développement

Ce projet utilise [uv](https://docs.astral.sh/uv/) pour la gestion de
l'environnement et des dépendances.

```bash
uv sync                # installe le paquet et les dépendances de dev
uv run pytest          # tests
uv run ruff check .    # lint
uv run ruff format .   # formatage
```

## Historique des versions

Voir [CHANGELOG.md](CHANGELOG.md).

## Licence

Distribué sous licence MIT. Voir le fichier [LICENCE](LICENCE).
