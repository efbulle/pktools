# pktools

Modules de manipulation de pk (points kilométriques) et de tronçons.

**pktools** est un paquet Python spécialisé dans la gestion des points kilométriques (PK), un système de référençage linéaire utilisé pour le réseau ferroviaire. Il fournit des outils pour convertir entre différentes représentations de PK et manipuler des ensembles de tronçons.

## Installation

### Prérequis

- Python ≥ 3.12

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

## Dépendances

- **polars** (≥1.38.1) : Framework de manipulation de données haute performance

## Licence

Voir le fichier [LICENSE](LICENCE).
