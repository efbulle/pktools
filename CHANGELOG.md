# Changelog

Toutes les modifications notables de ce projet seront documentées dans ce
fichier.

Le format est basé sur [Keep a Changelog](https://keepachangelog.com/fr/1.1.0/),
et ce projet adhère au [Semantic Versioning](https://semver.org/lang/fr/).

## [0.12.0] - Non publiée

### Ajouté

- Conversions strictes de PK pour les séries pandas, indépendantes de Polars.

### Modifié

- **Rupture à l'installation :** Polars n'est plus installé par défaut.
  Installer l'extra `polars` pour conserver les fonctions Polars habituelles ;
  l'extra `pandas` installe uniquement le backend pandas. Voir les instructions
  d'installation depuis ce dépôt dans le README.

## [0.11.0] - Première publication publique

- Première version publiée sur GitHub.
- Conversions de points kilométriques (`conv`) : PK internes, externes, métriques.
- Manipulation de tronçons (`tools`) : zones homogènes, composantes connexes,
  détection de chevauchements.
