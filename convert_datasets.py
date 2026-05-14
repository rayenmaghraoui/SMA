"""
Transformation des datasets vente → format attendu par SMA Assistant.

Datasets source  : C:\\Users\\rayen\\Desktop\\testing_data\\
Datasets sortie  : data\\ (remplace les fichiers par défaut)

Usage :
    python convert_datasets.py
"""

import pandas as pd
import numpy as np
from pathlib import Path

SRC = Path(r"C:\Users\rayen\Desktop\testing_data")
DST = Path(__file__).parent / "data"
DST.mkdir(exist_ok=True)

# ─────────────────────────────────────────────
# Chargement du dataset principal
# ─────────────────────────────────────────────
print("Chargement de 01_donnees_vente.csv …")
df = pd.read_csv(SRC / "01_donnees_vente.csv", parse_dates=["sale_date"])
df["month"] = df["sale_date"].dt.to_period("M").dt.to_timestamp()

# ─────────────────────────────────────────────
# 1. FINANCE  →  01_finance_performance.csv
# ─────────────────────────────────────────────
print("Génération finance …")
fin = (
    df.groupby("month")
    .agg(
        revenue=("revenue_tnd", "sum"),
        profit=("estimated_profit", "sum"),
    )
    .reset_index()
    .rename(columns={"month": "date"})
)
fin["cost"] = (fin["revenue"] - fin["profit"]).round(2)
fin["revenue"] = fin["revenue"].round(2)
fin["profit"] = fin["profit"].round(2)

# growth_rate = variation % du revenue par rapport au mois précédent
fin["growth_rate"] = fin["revenue"].pct_change().mul(100).round(2)
fin["growth_rate"] = fin["growth_rate"].fillna(0.0)

fin["date"] = fin["date"].dt.strftime("%Y-%m-%d")
fin = fin[["date", "revenue", "cost", "profit", "growth_rate"]]

out_fin = DST / "01_finance_performance.csv"
fin.to_csv(out_fin, index=False)
print(f"  ✓ {out_fin}  ({len(fin)} lignes)")

# ─────────────────────────────────────────────
# 2. MARKETING  →  02_marketing_campaigns.csv
# ─────────────────────────────────────────────
print("Génération marketing …")
mkt_raw = (
    df.groupby(["month", "sales_channel"])
    .agg(
        revenue=("revenue_tnd", "sum"),
        conversions=("invoice_id", "count"),
    )
    .reset_index()
)

# budget estimé = 15 % du CA généré (hypothèse standard e-commerce)
mkt_raw["budget"] = (mkt_raw["revenue"] * 0.15).round(2)

# clics estimés : taux de conversion moyen e-commerce ≈ 2-4 %
# → clics = conversions / 0.03
mkt_raw["clicks"] = (mkt_raw["conversions"] / 0.03).round(0).astype(int)
mkt_raw["conversion_rate"] = (
    mkt_raw["conversions"] / mkt_raw["clicks"] * 100
).round(2)

# campaign_id  = canal_AAAA_MM
mkt_raw["campaign_id"] = (
    mkt_raw["sales_channel"].str.replace(" ", "_")
    + "_"
    + mkt_raw["month"].dt.strftime("%Y_%m")
)

mkt = mkt_raw.rename(columns={"month": "date", "sales_channel": "channel"})
mkt["date"] = mkt["date"].dt.strftime("%Y-%m-%d")
mkt = mkt[["date", "campaign_id", "channel", "budget", "clicks", "conversions", "conversion_rate"]]

out_mkt = DST / "02_marketing_campaigns.csv"
mkt.to_csv(out_mkt, index=False)
print(f"  ✓ {out_mkt}  ({len(mkt)} lignes)")

# ─────────────────────────────────────────────
# 3. SUPPORT  →  03_customer_support.csv
# ─────────────────────────────────────────────
# Support synthétisé depuis les commandes :
# - chaque transaction devient un ticket potentiel (taux incident ≈ 8 %)
# - issue_type dérivé de la catégorie produit
# - satisfaction corrélée à la marge
# - churn_risk inversement proportionnel au nombre de commandes du client
print("Génération support …")

ISSUE_MAP = {
    "Electronique": "Panne technique",
    "Mobilier":     "Livraison endommagée",
    "Textile":      "Retour produit",
    "Alimentaire":  "Qualité produit",
    "Fournitures":  "Délai livraison",
    "Divers":       "Autre",
}

rng = np.random.default_rng(42)

# Nb achats par client → proxy de fidélité
purchases_per_client = df.groupby("customer_id")["invoice_id"].count().rename("nb_purchases")
df2 = df.merge(purchases_per_client, on="customer_id")

# Filtre : ~8 % des transactions génèrent un ticket support
mask = rng.random(len(df2)) < 0.08
sup_raw = df2[mask].copy().reset_index(drop=True)

sup_raw["ticket_id"] = ["TKT" + str(i).zfill(5) for i in range(1, len(sup_raw) + 1)]
sup_raw["issue_type"] = sup_raw["category"].map(ISSUE_MAP).fillna("Autre")

# resolution_hours : entre 1h et 72h, plus courts pour produits chers (meilleur SAV)
margin_ratio = (sup_raw["estimated_profit"] / sup_raw["revenue_tnd"]).clip(0.01, 0.99)
sup_raw["resolution_hours"] = (
    rng.uniform(1, 72, len(sup_raw)) * (1 - margin_ratio * 0.5)
).round(1)

# satisfaction_score : 1-5, corrélé à la marge et au nombre d'achats
base_score = 2.5 + margin_ratio * 1.5 + np.log1p(sup_raw["nb_purchases"]) * 0.3
sup_raw["satisfaction_score"] = (
    base_score + rng.normal(0, 0.3, len(sup_raw))
).clip(1, 5).round(1)

# churn_risk : 0-1, clients avec peu d'achats = risque plus élevé
max_pur = sup_raw["nb_purchases"].max()
sup_raw["churn_risk"] = (
    1 - (sup_raw["nb_purchases"] / max_pur) ** 0.5
    + rng.uniform(-0.1, 0.1, len(sup_raw))
).clip(0, 1).round(2)

sup = sup_raw[["sale_date", "ticket_id", "issue_type", "resolution_hours", "satisfaction_score", "churn_risk"]].copy()
sup = sup.rename(columns={"sale_date": "date"})
sup["date"] = pd.to_datetime(sup["date"]).dt.strftime("%Y-%m-%d")

out_sup = DST / "03_customer_support.csv"
sup.to_csv(out_sup, index=False)
print(f"  ✓ {out_sup}  ({len(sup)} lignes)")

# ─────────────────────────────────────────────
# Résumé
# ─────────────────────────────────────────────
print("\n── Résumé des fichiers générés ──")
for p in [out_fin, out_mkt, out_sup]:
    d = pd.read_csv(p)
    print(f"  {p.name:35s}  {len(d):4d} lignes  colonnes: {list(d.columns)}")
print("\nTransformation terminée. Redémarre le backend pour prendre en compte les nouveaux fichiers.")
