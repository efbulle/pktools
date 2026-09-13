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
pip install pktools
```

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

## Dépendances

- **polars** (≥1.38.1) : Framework de manipulation de données haute performance

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
