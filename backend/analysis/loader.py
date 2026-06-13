"""
Chargement, validation et nettoyage des cinq datasets CSV du projet.

Les fichiers attendus (définis dans config.py) :
    - 01_donnees_vente.csv
    - 02_analyse_region.csv
    - 03_analyse_categorie.csv
    - 04_analyse_canaux.csv
    - 05_kpis_globaux.csv

Usage direct (debug) :
    python -m backend.analysis.loader
"""

import logging
import sys
from pathlib import Path
from typing import Any, Dict, Optional

import pandas as pd

# Ajout de la racine au chemin si lancé en direct
if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from backend.config import (
    UPLOADS_DIR,
    VENTES_CSV,
    REGIONS_CSV,
    CATEGORIES_CSV,
    CANAUX_CSV,
    KPIS_CSV,
    DEBUG,
)

# ============================================================
# Configuration du logging
# ============================================================

logging.basicConfig(
    level=logging.DEBUG if DEBUG else logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


# ============================================================
# Schémas attendus par dataset
# ============================================================

VENTES_SCHEMA: Dict[str, type] = {
    "invoice_id": str,
    "product_name": str,
    "category": str,
    "quantity": int,
    "unit_price_tnd": float,
    "revenue_tnd": float,
    "customer_id": str,
    "customer_region": str,
    "sale_date": str,
    "sales_channel": str,
    "payment_method": str,
    "estimated_profit": float,
}

REGIONS_SCHEMA: Dict[str, type] = {
    "customer_region": str,
    "ca_total": float,
    "profit_total": float,
    "nb_transactions": int,
    "panier_moyen": float,
}

CATEGORIES_SCHEMA: Dict[str, type] = {
    "category": str,
    "ca_total": float,
    "profit_total": float,
    "nb_transactions": int,
    "quantite_vendue": int,
    "prix_moyen": float,
}

CANAUX_SCHEMA: Dict[str, type] = {
    "sales_channel": str,
    "ca_total": float,
    "nb_transactions": int,
    "panier_moyen": float,
}

KPIS_SCHEMA: Dict[str, type] = {
    "indicateur": str,
    "valeur": float,
}


# ============================================================
# Fonctions utilitaires
# ============================================================

def _validate_columns(df: pd.DataFrame, schema: Dict[str, type], name: str) -> None:
    """
    Vérifie que toutes les colonnes attendues sont présentes dans le DataFrame.

    Args:
        df:     DataFrame à valider.
        schema: Dictionnaire {nom_colonne: type_attendu}.
        name:   Nom du dataset (pour les messages d'erreur).

    Raises:
        ValueError: Si des colonnes requises sont absentes.
    """
    expected = set(schema.keys())
    actual = set(df.columns.str.strip().str.lower())
    missing = expected - actual
    if missing:
        raise ValueError(
            f"[{name}] Colonnes manquantes : {sorted(missing)}. "
            f"Colonnes présentes : {sorted(actual)}"
        )
    logger.debug("[%s] Validation des colonnes OK — %d colonnes présentes", name, len(expected))


def _clean_ventes(df: pd.DataFrame) -> pd.DataFrame:
    """
    Nettoie et type le dataset des ventes (01_donnees_vente.csv).
    Colonnes : invoice_id, product_name, category, quantity, unit_price_tnd,
               revenue_tnd, customer_id, customer_region, sale_date,
               sales_channel, payment_method, estimated_profit
    """
    df = df.copy()
    df.columns = df.columns.str.strip().str.lower()
    if "sale_date" not in df.columns and "_unmapped_sale_date" in df.columns:
        df = df.rename(columns={"_unmapped_sale_date": "sale_date"})
    df["sale_date"] = pd.to_datetime(df["sale_date"], format="%Y-%m-%d", errors="coerce")
    df["product_name"] = df["product_name"].astype(str).str.strip()
    df["category"] = df["category"].astype(str).str.strip()
    df["customer_region"] = df["customer_region"].astype(str).str.strip()
    df["sales_channel"] = df["sales_channel"].astype(str).str.strip()
    df["payment_method"] = df["payment_method"].astype(str).str.strip()
    df["revenue_tnd"] = pd.to_numeric(df["revenue_tnd"], errors="coerce")
    df["unit_price_tnd"] = pd.to_numeric(df["unit_price_tnd"], errors="coerce")
    df["estimated_profit"] = pd.to_numeric(df["estimated_profit"], errors="coerce")
    df["quantity"] = pd.to_numeric(df["quantity"], errors="coerce").round().astype("Int64")
    if df["sale_date"].isna().any():
        df = df.dropna(subset=["sale_date"])
    for col in ["revenue_tnd", "unit_price_tnd", "estimated_profit"]:
        if df[col].isna().any():
            df[col] = df[col].fillna(df[col].median())
    if df["quantity"].isna().any():
        df["quantity"] = df["quantity"].fillna(int(df["quantity"].median()))
    df = df.sort_values("sale_date").reset_index(drop=True)
    logger.info("[ventes] Nettoyage terminé — %d lignes", len(df))
    return df


def _clean_regions(df: pd.DataFrame) -> pd.DataFrame:
    """
    Nettoie et type le dataset régional (02_analyse_region.csv).
    Colonnes : customer_region, CA_Total, Profit_Total, Nb_Transactions, Panier_Moyen
    """
    df = df.copy()
    df.columns = df.columns.str.strip().str.lower()
    df["customer_region"] = df["customer_region"].astype(str).str.strip()
    df["ca_total"] = pd.to_numeric(df["ca_total"], errors="coerce")
    df["profit_total"] = pd.to_numeric(df["profit_total"], errors="coerce")
    df["nb_transactions"] = pd.to_numeric(df["nb_transactions"], errors="coerce").round().astype("Int64")
    df["panier_moyen"] = pd.to_numeric(df["panier_moyen"], errors="coerce")
    for col in ["ca_total", "profit_total", "panier_moyen"]:
        if df[col].isna().any():
            df[col] = df[col].fillna(df[col].median())
    logger.info("[regions] Nettoyage terminé — %d lignes", len(df))
    return df


def _clean_categories(df: pd.DataFrame) -> pd.DataFrame:
    """
    Nettoie et type le dataset des catégories (03_analyse_categorie.csv).
    Colonnes : category, CA_Total, Profit_Total, Nb_Transactions, Quantite_Vendue, Prix_Moyen
    """
    df = df.copy()
    df.columns = df.columns.str.strip().str.lower()
    df["category"] = df["category"].astype(str).str.strip()
    df["ca_total"] = pd.to_numeric(df["ca_total"], errors="coerce")
    df["profit_total"] = pd.to_numeric(df["profit_total"], errors="coerce")
    df["nb_transactions"] = pd.to_numeric(df["nb_transactions"], errors="coerce").round().astype("Int64")
    df["quantite_vendue"] = pd.to_numeric(df["quantite_vendue"], errors="coerce").round().astype("Int64")
    df["prix_moyen"] = pd.to_numeric(df["prix_moyen"], errors="coerce")
    for col in ["ca_total", "profit_total", "prix_moyen"]:
        if df[col].isna().any():
            df[col] = df[col].fillna(df[col].median())
    logger.info("[categories] Nettoyage terminé — %d lignes", len(df))
    return df


def _clean_canaux(df: pd.DataFrame) -> pd.DataFrame:
    """
    Nettoie et type le dataset des canaux (04_analyse_canaux.csv).
    Colonnes : sales_channel, CA_Total, Nb_Transactions, Panier_Moyen
    """
    df = df.copy()
    df.columns = df.columns.str.strip().str.lower()
    df["sales_channel"] = df["sales_channel"].astype(str).str.strip()
    df["ca_total"] = pd.to_numeric(df["ca_total"], errors="coerce")
    df["nb_transactions"] = pd.to_numeric(df["nb_transactions"], errors="coerce").round().astype("Int64")
    df["panier_moyen"] = pd.to_numeric(df["panier_moyen"], errors="coerce")
    for col in ["ca_total", "panier_moyen"]:
        if df[col].isna().any():
            df[col] = df[col].fillna(df[col].median())
    logger.info("[canaux] Nettoyage terminé — %d lignes", len(df))
    return df


def _clean_kpis(df: pd.DataFrame) -> pd.DataFrame:
    """
    Nettoie et type le dataset des KPIs globaux (05_kpis_globaux.csv).
    Colonnes : Indicateur, Valeur  (format clé-valeur)
    """
    df = df.copy()
    df.columns = df.columns.str.strip().str.lower()
    df["indicateur"] = df["indicateur"].astype(str).str.strip()
    df["valeur"] = pd.to_numeric(df["valeur"], errors="coerce").fillna(0.0)
    logger.info("[kpis] Nettoyage terminé — %d lignes", len(df))
    return df


# ============================================================
# Fonction principale
# ============================================================

def load_datasets(data_dir: Optional[Path] = None) -> Dict[str, pd.DataFrame]:
    """
    Charge, valide et nettoie les cinq datasets CSV du projet.

    Les fichiers attendus dans data_dir :
        - 01_donnees_vente.csv
        - 02_analyse_region.csv
        - 03_analyse_categorie.csv
        - 04_analyse_canaux.csv
        - 05_kpis_globaux.csv

    Args:
        data_dir: Répertoire contenant les CSV.
                  Si None, utilise UPLOADS_DIR défini dans config.py.

    Returns:
        dict avec les clés "ventes", "regions", "categories", "canaux", "kpis".

    Raises:
        FileNotFoundError: Si un fichier CSV est introuvable.
        ValueError:        Si un dataset ne contient pas les colonnes attendues.
    """
    if data_dir is not None:
        resolved_dir = Path(data_dir)
        ventes_path = resolved_dir / VENTES_CSV.name
        regions_path = resolved_dir / REGIONS_CSV.name
        categories_path = resolved_dir / CATEGORIES_CSV.name
        canaux_path = resolved_dir / CANAUX_CSV.name
        kpis_path = resolved_dir / KPIS_CSV.name
    else:
        resolved_dir = UPLOADS_DIR
        ventes_path = VENTES_CSV
        regions_path = REGIONS_CSV
        categories_path = CATEGORIES_CSV
        canaux_path = CANAUX_CSV
        kpis_path = KPIS_CSV

    logger.info("Chargement des datasets depuis : %s", resolved_dir)

    datasets: Dict[str, pd.DataFrame] = {}

    if not ventes_path.exists():
        raise FileNotFoundError(f"Fichier introuvable : {ventes_path}")
    logger.info("Chargement du fichier ventes : %s", ventes_path)
    df_ventes = pd.read_csv(ventes_path)
    _validate_columns(df_ventes, VENTES_SCHEMA, "ventes")
    datasets["ventes"] = _clean_ventes(df_ventes)

    if not regions_path.exists():
        raise FileNotFoundError(f"Fichier introuvable : {regions_path}")
    logger.info("Chargement du fichier regions : %s", regions_path)
    df_regions = pd.read_csv(regions_path)
    _validate_columns(df_regions, REGIONS_SCHEMA, "regions")
    datasets["regions"] = _clean_regions(df_regions)

    if not categories_path.exists():
        raise FileNotFoundError(f"Fichier introuvable : {categories_path}")
    logger.info("Chargement du fichier categories : %s", categories_path)
    df_categories = pd.read_csv(categories_path)
    _validate_columns(df_categories, CATEGORIES_SCHEMA, "categories")
    datasets["categories"] = _clean_categories(df_categories)

    if not canaux_path.exists():
        raise FileNotFoundError(f"Fichier introuvable : {canaux_path}")
    logger.info("Chargement du fichier canaux : %s", canaux_path)
    df_canaux = pd.read_csv(canaux_path)
    _validate_columns(df_canaux, CANAUX_SCHEMA, "canaux")
    datasets["canaux"] = _clean_canaux(df_canaux)

    if not kpis_path.exists():
        raise FileNotFoundError(f"Fichier introuvable : {kpis_path}")
    logger.info("Chargement du fichier kpis : %s", kpis_path)
    df_kpis = pd.read_csv(kpis_path)
    _validate_columns(df_kpis, KPIS_SCHEMA, "kpis")
    datasets["kpis"] = _clean_kpis(df_kpis)

    logger.info(
        "Datasets chargés avec succès — ventes: %d | regions: %d | categories: %d | canaux: %d | kpis: %d",
        len(datasets["ventes"]),
        len(datasets["regions"]),
        len(datasets["categories"]),
        len(datasets["canaux"]),
        len(datasets["kpis"]),
    )
    return datasets


def _deserialize_datasets(raw_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convertit les données brutes (dict/list) en DataFrames Pandas.

    Args:
        raw_data: Dictionnaire contenant les données sérialisées.

    Returns:
        Dictionnaire avec les DataFrames pour chaque dataset.
    """
    import pandas as pd

    datasets = {}
    for key in ["ventes", "regions", "categories", "canaux", "kpis"]:
        if key in raw_data:
            data = raw_data[key]
            if isinstance(data, pd.DataFrame):
                datasets[key] = data
            elif isinstance(data, dict):
                datasets[key] = pd.DataFrame(data)
            elif isinstance(data, list):
                datasets[key] = pd.DataFrame(data)
            else:
                raise ValueError(f"Format non supporté pour {key}: {type(data)}")
    return datasets


def load_uploaded_datasets(upload_dir: Optional[Path] = None) -> Dict[str, pd.DataFrame]:
    """
    Charge, valide et nettoie les datasets depuis le dossier uploads.

    Args:
        upload_dir: Dossier des fichiers uploadés. Si None, utilise UPLOADS_DIR.

    Returns:
        dict avec les clés "ventes", "regions", "categories", "canaux", "kpis".

    Raises:
        FileNotFoundError: Si un des cinq datasets est introuvable.
        ValueError: Si un fichier trouvé ne respecte pas le schéma attendu.
    """
    resolved_dir = Path(upload_dir) if upload_dir is not None else UPLOADS_DIR
    return load_datasets(resolved_dir)


# ============================================================
# Exécution directe — affichage debug
# ============================================================

if __name__ == "__main__":
    try:
        resolved_dir = UPLOADS_DIR
        logger.info("=== Mode debug — répertoire : %s ===", resolved_dir)
        datasets = load_datasets(resolved_dir)

        labels = {
            "ventes": "01_donnees_vente.csv",
            "regions": "02_analyse_region.csv",
            "categories": "03_analyse_categorie.csv",
            "canaux": "04_analyse_canaux.csv",
            "kpis": "05_kpis_globaux.csv",
        }

        for key, df in datasets.items():
            sep = "=" * 60
            print(f"\n{sep}")
            print(f"  Dataset : {labels[key]}")
            print(sep)
            print(f"  Shape   : {df.shape[0]} lignes x {df.shape[1]} colonnes")
            print("\n  Dtypes :")
            for col, dtype in df.dtypes.items():
                print(f"    {col:<25} {dtype}")
            print("\n  head(3) :")
            print(df.head(3).to_string(index=False))
            print()

    except (FileNotFoundError, ValueError) as exc:
        logger.error("Erreur lors du chargement des datasets : %s", exc)
        sys.exit(1)
