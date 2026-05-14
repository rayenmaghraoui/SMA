# Tunisia Business Datasets — Guide de référence rapide

## Résumé

Cinq jeux de données prêts pour le système AI Business Consultant :

```
1. Données de vente détaillées      (2 000 transactions)
2. Analyse par région               (agrégation par gouvernorat)
3. Analyse par catégorie produit    (5 catégories)
4. Analyse par canal de vente       (4 canaux)
5. KPIs globaux agrégés             (indicateurs financiers)
```

---

## Fichiers

### Datasets (dans `data/uploads/`)
```
01_donnees_vente.csv          ~200 KB    2 000 transactions
02_analyse_region.csv           ~5 KB    1 ligne / région
03_analyse_categorie.csv        ~2 KB    5 catégories
04_analyse_canaux.csv           ~1 KB    4 canaux
05_kpis_globaux.csv             ~1 KB    KPIs agrégés
```

### Code & Documentation
```
tunisia_data_pipeline.py       Script de génération des données
data_analysis_examples.py      Exemples d'analyse
DATASETS_DOCUMENTATION.md      Documentation technique complète
QUICK_REFERENCE.md             Ce fichier
FINAL_SUMMARY_REPORT.md        Rapport de complétion
```

---

## Chargement rapide

```python
import pandas as pd

ventes     = pd.read_csv('data/uploads/01_donnees_vente.csv')
regions    = pd.read_csv('data/uploads/02_analyse_region.csv')
categories = pd.read_csv('data/uploads/03_analyse_categorie.csv')
canaux     = pd.read_csv('data/uploads/04_analyse_canaux.csv')
kpis       = pd.read_csv('data/uploads/05_kpis_globaux.csv')

print("Transactions :", len(ventes))       # 2 000
print("Régions :", len(regions))           # ~9
print("Catégories :", len(categories))     # 5
print("Canaux :", len(canaux))             # 4
print("KPIs globaux :", len(kpis))        # 4
```

### Via le loader du projet
```python
from backend.analysis.loader import load_datasets

datasets = load_datasets()
# Clés disponibles : "ventes", "regions", "categories", "canaux", "kpis"
```

---

## Vue d'ensemble des datasets

### Dataset 1 : Données de vente
| Métrique | Valeur |
|----------|--------|
| Enregistrements | 2 000 transactions |
| CA total | 2 191 187 TND |
| Profit total | 547 796 TND |
| Régions | Tunis, Ariana, Sfax, Sousse… |

### Dataset 2 : Analyse par région
| Métrique | Valeur |
|----------|--------|
| Top région (CA) | Tunis (598 464 TND) |
| Meilleur panier | Ariana (1 261 TND) |
| Nb régions | ~9 gouvernorats |

### Dataset 3 : Analyse par catégorie
| Métrique | Valeur |
|----------|--------|
| Top catégorie (CA) | Mobilier (962 496 TND) |
| Top catégorie (quantité) | Textile (2 012 unités) |
| Nb catégories | 5 |

### Dataset 4 : Analyse par canal
| Métrique | Valeur |
|----------|--------|
| Top canal (CA) | Magasin physique (812 411 TND) |
| Meilleur panier | Réseaux sociaux (1 358 TND) |
| Nb canaux | 4 |

### Dataset 5 : KPIs globaux
| Indicateur | Valeur |
|-----------|--------|
| CA Total | 2 191 187 TND |
| Profit Total | 547 796 TND |
| Nb Transactions | 2 000 |
| Panier Moyen | 1 095 TND |

---

## Analyses rapides

```python
# Meilleure région par CA
regions.sort_values('CA_Total', ascending=False).head(3)

# Marge bénéficiaire par catégorie
categories['marge'] = categories['Profit_Total'] / categories['CA_Total'] * 100
print(categories[['category', 'marge']])

# Panier moyen par canal
canaux.sort_values('Panier_Moyen', ascending=False)

# Répartition des ventes par canal (depuis ventes détaillées)
ventes.groupby('sales_channel')['revenue_tnd'].sum().sort_values(ascending=False)

# Top 5 produits
ventes.groupby('product_name')['revenue_tnd'].sum().sort_values(ascending=False).head(5)
```

---

## Chemins des fichiers

```
ai-business-consultant/
├── data/
│   └── uploads/
│       ├── 01_donnees_vente.csv
│       ├── 02_analyse_region.csv
│       ├── 03_analyse_categorie.csv
│       ├── 04_analyse_canaux.csv
│       └── 05_kpis_globaux.csv
└── data_setup/
    ├── DATASETS_DOCUMENTATION.md
    ├── QUICK_REFERENCE.md
    ├── FINAL_SUMMARY_REPORT.md
    ├── tunisia_data_pipeline.py
    └── data_analysis_examples.py
```

**Statut : MIGRÉ VERS 5 DATASETS**
