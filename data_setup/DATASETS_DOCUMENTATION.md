# Tunisia Business Data Pipeline — Documentation Technique

## Résumé

Ce projet fournit **5 jeux de données de production** basés sur des données commerciales tunisiennes réelles.
Ils sont conçus pour le système multi-agents AI Business Consultant (PFE).

---

## DATASET 1 : Données de vente (01_donnees_vente.csv)

**Fichier :** `data/uploads/01_donnees_vente.csv`  
**Enregistrements :** 2 000 transactions individuelles

### Colonnes

| Colonne | Type | Description |
|---------|------|-------------|
| invoice_id | string | Identifiant unique de la facture (INV00001…) |
| product_name | string | Nom du produit vendu |
| category | string | Catégorie produit (Mobilier, Electronique, Divers, Textile, Fournitures) |
| quantity | integer | Quantité commandée |
| unit_price_tnd | float | Prix unitaire en TND |
| revenue_tnd | float | Chiffre d'affaires = quantité × prix unitaire |
| customer_id | string | Identifiant client |
| customer_region | string | Région du client (Tunis, Ariana, Sfax, Sousse…) |
| sale_date | string | Date de vente (YYYY-MM-DD) |
| sales_channel | string | Canal de vente (Magasin physique, Site web, Application mobile, Réseaux sociaux) |
| payment_method | string | Méthode de paiement (Carte bancaire, Espèces, Virement) |
| estimated_profit | float | Profit estimé = revenue_tnd × 0.25 |

### Exemple
```
invoice_id  product_name   category     quantity  unit_price_tnd  revenue_tnd  customer_region  sales_channel      payment_method   estimated_profit
INV00001    Montre Casio   Divers       5         61.25           306.25       Tunis            Magasin physique   Carte bancaire   76.56
INV00002    Classeur       Fournitures  1         15.25           15.25        Tunis            Magasin physique   Especes          3.81
INV00003    Table en Bois  Mobilier     6         479.25          2875.50      Ariana           Site web           Virement         718.87
```

---

## DATASET 2 : Analyse par région (02_analyse_region.csv)

**Fichier :** `data/uploads/02_analyse_region.csv`  
**Enregistrements :** 1 ligne par région (agrégation complète)

### Colonnes

| Colonne | Type | Description |
|---------|------|-------------|
| customer_region | string | Nom de la région |
| CA_Total | float | Chiffre d'affaires total (TND) |
| Profit_Total | float | Profit total (TND) |
| Nb_Transactions | integer | Nombre de transactions |
| Panier_Moyen | float | Panier moyen = CA_Total / Nb_Transactions (TND) |

### Données complètes
```
customer_region  CA_Total (TND)  Profit_Total (TND)  Nb_Transactions  Panier_Moyen (TND)
Tunis            598 464         149 615              506              1 182
Ariana           328 069          82 017              260              1 261
Sfax             311 032          77 758              303              1 026
Sousse           237 515          59 378              230              1 032
Ben Arous        179 289          44 822              177              1 012
Monastir         152 060          38 015              142              1 070
Gabès             98 765          24 691               98              1 007
Nabeul            81 472          20 368               87                936
Bizerte            ...
```

---

## DATASET 3 : Analyse par catégorie (03_analyse_categorie.csv)

**Fichier :** `data/uploads/03_analyse_categorie.csv`  
**Enregistrements :** 1 ligne par catégorie

### Colonnes

| Colonne | Type | Description |
|---------|------|-------------|
| category | string | Nom de la catégorie produit |
| CA_Total | float | Chiffre d'affaires total (TND) |
| Profit_Total | float | Profit total (TND) |
| Nb_Transactions | integer | Nombre de transactions |
| Quantite_Vendue | integer | Quantité totale vendue |
| Prix_Moyen | float | Prix moyen par transaction (TND) |

### Données complètes
```
category      CA_Total (TND)  Profit_Total (TND)  Nb_Transactions  Quantite_Vendue  Prix_Moyen (TND)
Mobilier       962 496         240 624              347              1 906             496
Electronique   919 233         229 808              362              2 032             457
Divers         137 291          34 322              278              1 599              85
Textile        117 093          29 273              370              2 012              59
Fournitures     54 074          13 518              217              1 405              43
```

**Note :** Mobilier et Electronique représentent ~86% du CA total.

---

## DATASET 4 : Analyse par canal (04_analyse_canaux.csv)

**Fichier :** `data/uploads/04_analyse_canaux.csv`  
**Enregistrements :** 1 ligne par canal de vente

### Colonnes

| Colonne | Type | Description |
|---------|------|-------------|
| sales_channel | string | Canal de vente |
| CA_Total | float | Chiffre d'affaires total (TND) |
| Nb_Transactions | integer | Nombre de transactions |
| Panier_Moyen | float | Panier moyen = CA_Total / Nb_Transactions (TND) |

### Données complètes
```
sales_channel      CA_Total (TND)  Nb_Transactions  Panier_Moyen (TND)
Magasin physique   812 411          779              1 042
Site web           668 056          591              1 130
Application mobile 433 491          426              1 017
Réseaux sociaux    277 228          204              1 358
```

**Note :** Le canal Réseaux sociaux génère le panier moyen le plus élevé (1 358 TND).

---

## DATASET 5 : KPIs globaux (05_kpis_globaux.csv)

**Fichier :** `data/uploads/05_kpis_globaux.csv`  
**Enregistrements :** Indicateurs agrégés (format clé-valeur)

### Colonnes

| Colonne | Type | Description |
|---------|------|-------------|
| Indicateur | string | Nom de l'indicateur KPI |
| Valeur | string | Valeur de l'indicateur |

### Données complètes
```
Indicateur              Valeur
CA Total (TND)          2 191 187
Profit Total (TND)        547 796
Nb Transactions           2 000
Panier Moyen (TND)        1 095
```

---

## Chargement dans le projet

### Via le loader
```python
from backend.analysis.loader import load_datasets

datasets = load_datasets()
# datasets["ventes"]     -> DataFrame 01_donnees_vente.csv
# datasets["regions"]    -> DataFrame 02_analyse_region.csv
# datasets["categories"] -> DataFrame 03_analyse_categorie.csv
# datasets["canaux"]     -> DataFrame 04_analyse_canaux.csv
# datasets["kpis"]       -> DataFrame 05_kpis_globaux.csv
```

### Chargement direct
```python
import pandas as pd

ventes     = pd.read_csv('data/uploads/01_donnees_vente.csv')
regions    = pd.read_csv('data/uploads/02_analyse_region.csv')
categories = pd.read_csv('data/uploads/03_analyse_categorie.csv')
canaux     = pd.read_csv('data/uploads/04_analyse_canaux.csv')
kpis       = pd.read_csv('data/uploads/05_kpis_globaux.csv')
```

---

## KPIs calculés par les analyseurs

### kpis_analyzer.py (depuis 05_kpis_globaux.csv)
- `revenue_total` : CA total (TND)
- `profit_total` : Profit total (TND)
- `profit_margin` : Marge bénéficiaire (%)
- `trend` : Tendance calculée

### canaux_analyzer.py (depuis 04_analyse_canaux.csv)
- `best_channel` : Canal avec le meilleur CA
- `top_panier_channel` : Canal avec le panier moyen le plus élevé
- `revenue_by_channel` : Dict CA par canal
- `total_ca` : CA total tous canaux

### categories_analyzer.py (depuis 03_analyse_categorie.csv)
- `top_category_by_revenue` : Meilleure catégorie par CA
- `top_category_by_quantity` : Meilleure catégorie par quantité
- `revenue_by_category` : Dict CA par catégorie

---

## Contexte tunisien

- **Monnaie :** Dinar Tunisien (TND)
- **Régions couvertes :** Tunis, Ariana, Sfax, Sousse, Ben Arous, Monastir, Gabès, Nabeul, Bizerte
- **Canaux :** Magasin physique, Site web, Application mobile, Réseaux sociaux
- **Catégories :** Mobilier, Electronique, Divers, Textile, Fournitures
- **Méthodes de paiement :** Carte bancaire, Espèces, Virement

**Statut : MIGRÉ VERS 5 DATASETS**
