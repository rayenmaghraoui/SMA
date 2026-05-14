# Tunisia Business Data Pipeline - Complete Guide

## Project Overview

This project generates **5 production-ready business datasets** based on real Tunisian business data. The datasets are designed for the AI Business Consultant multi-agent system, covering sales, regional performance, product categories, marketing channels, and global KPIs.

---

## Deliverables

### Generated Datasets (CSV Format)

| File | Description | Colonnes clés |
|------|-------------|---------------|
| `01_donnees_vente.csv` | Transactions de vente détaillées | invoice_id, product_name, category, quantity, unit_price_tnd, revenue_tnd, customer_id, customer_region, sale_date, sales_channel, payment_method, estimated_profit |
| `02_analyse_region.csv` | Performance par région | customer_region, CA_Total, Profit_Total, Nb_Transactions, Panier_Moyen |
| `03_analyse_categorie.csv` | Performance par catégorie produit | category, CA_Total, Profit_Total, Nb_Transactions, Quantite_Vendue, Prix_Moyen |
| `04_analyse_canaux.csv` | Performance par canal de vente | sales_channel, CA_Total, Nb_Transactions, Panier_Moyen |
| `05_kpis_globaux.csv` | Indicateurs globaux agrégés | Indicateur, Valeur |

### Code & Documentation

| File | Purpose |
|------|---------|
| `tunisia_data_pipeline.py` | Script de génération des données |
| `data_analysis_examples.py` | Exemples d'analyse et de business intelligence |
| `DATASETS_DOCUMENTATION.md` | Documentation technique complète |
| `README.md` | Ce fichier |

---

## Dataset Descriptions

### DATASET 1 : Données de vente (01_donnees_vente.csv)

Transactions individuelles de vente avec détail produit, région, canal et profit estimé.

**Exemple de données :**
```
invoice_id  product_name   category     quantity  unit_price_tnd  revenue_tnd  customer_region  sales_channel      payment_method
INV00001    Montre Casio   Divers       5         61.25           306.25       Tunis            Magasin physique   Carte bancaire
INV00002    Classeur       Fournitures  1         15.25           15.25        Tunis            Magasin physique   Especes
INV00003    Montre Casio   Divers       7         120.25          841.75       Tunis            Site web           Virement
INV00004    Table en Bois  Mobilier     6         479.25          2875.50      Ariana           Magasin physique   Virement
```

**Canaux de vente :** Magasin physique, Site web, Application mobile, Réseaux sociaux  
**Régions :** Tunis, Ariana, Sfax, Sousse, et autres gouvernorats  
**Méthodes de paiement :** Carte bancaire, Espèces, Virement

---

### DATASET 2 : Analyse par région (02_analyse_region.csv)

Agrégation du chiffre d'affaires, profit, nombre de transactions et panier moyen par région.

**Données :**
```
customer_region  CA_Total (TND)  Profit_Total (TND)  Nb_Transactions  Panier_Moyen (TND)
Tunis            598 464         149 615              506              1 182
Ariana           328 069          82 017              260              1 261
Sfax             311 032          77 758              303              1 026
Sousse           237 515          59 378              230              1 032
```

---

### DATASET 3 : Analyse par catégorie (03_analyse_categorie.csv)

Performance par catégorie de produit : revenu, profit, transactions, quantités et prix moyen.

**Données :**
```
category      CA_Total (TND)  Profit_Total (TND)  Nb_Transactions  Quantite_Vendue  Prix_Moyen (TND)
Mobilier       962 496         240 624              347              1 906             496
Electronique   919 233         229 808              362              2 032             457
Divers         137 291          34 322              278              1 599              85
Textile        117 093          29 273              370              2 012              59
```

---

### DATASET 4 : Analyse par canal (04_analyse_canaux.csv)

Performance commerciale par canal de distribution.

**Données :**
```
sales_channel      CA_Total (TND)  Nb_Transactions  Panier_Moyen (TND)
Magasin physique   812 411          779              1 042
Site web           668 056          591              1 130
Application mobile 433 491          426              1 017
Réseaux sociaux    277 228          204              1 358
```

---

### DATASET 5 : KPIs globaux (05_kpis_globaux.csv)

Indicateurs financiers agrégés sur toute la période d'analyse.

**Données :**
```
Indicateur              Valeur
CA Total (TND)          2 191 187
Profit Total (TND)        547 796
Nb Transactions           2 000
Panier Moyen (TND)        1 095
```

---

## Utilisation

### Chargement direct des fichiers
```python
import pandas as pd

ventes     = pd.read_csv('data/uploads/01_donnees_vente.csv')
regions    = pd.read_csv('data/uploads/02_analyse_region.csv')
categories = pd.read_csv('data/uploads/03_analyse_categorie.csv')
canaux     = pd.read_csv('data/uploads/04_analyse_canaux.csv')
kpis       = pd.read_csv('data/uploads/05_kpis_globaux.csv')
```

### Chargement via le loader du projet
```python
from backend.analysis.loader import load_datasets

datasets = load_datasets()
# datasets["ventes"]     -> 01_donnees_vente.csv
# datasets["regions"]    -> 02_analyse_region.csv
# datasets["categories"] -> 03_analyse_categorie.csv
# datasets["canaux"]     -> 04_analyse_canaux.csv
# datasets["kpis"]       -> 05_kpis_globaux.csv
```

---

## Chemins des fichiers

```
ai-business-consultant/
├── data/
│   └── uploads/
│       ├── 01_donnees_vente.csv       (transactions détaillées)
│       ├── 02_analyse_region.csv      (agrégation par région)
│       ├── 03_analyse_categorie.csv   (agrégation par catégorie)
│       ├── 04_analyse_canaux.csv      (agrégation par canal)
│       └── 05_kpis_globaux.csv        (KPIs financiers globaux)
└── data_setup/
    ├── tunisia_data_pipeline.py
    ├── data_analysis_examples.py
    ├── DATASETS_DOCUMENTATION.md
    └── README.md
```

---

## Contexte tunisien

- **Monnaie :** Dinar Tunisien (TND)
- **Régions couvertes :** Tunis, Ariana, Sfax, Sousse, et autres gouvernorats
- **Canaux :** Magasin physique, Site web, Application mobile, Réseaux sociaux
- **Catégories :** Mobilier, Electronique, Divers, Textile, Fournitures
- **Méthodes de paiement :** Carte bancaire, Espèces, Virement

---

**Statut : MIGRÉ VERS 5 DATASETS**
