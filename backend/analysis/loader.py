"""
Chargement, validation et nettoyage des trois datasets CSV du projet.

Les fichiers attendus (définis dans config.py) :
    - 01_finance_performance.csv
    - 02_marketing_campaigns.csv
    - 03_customer_support.csv

Usage direct (debug) :
    python -m backend.analysis.loader
"""

import logging
import sys
from pathlib import Path
from typing import Dict, Optional

import pandas as pd

# Ajout de la racine au chemin si lancé en direct
if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from backend.config import (
    DATA_DIR,
    FINANCE_CSV,
    MARKETING_CSV,
    SUPPORT_CSV,
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

FINANCE_SCHEMA: Dict[str, type] = {
    "date": str,
    "revenue": float,
    "cost": float,
    "profit": float,
    "growth_rate": float,
}

MARKETING_SCHEMA: Dict[str, type] = {
    "date": str,
    "campaign_id": str,
    "channel": str,
    "budget": float,
    "clicks": int,
    "conversions": int,
    "conversion_rate": float,
}

SUPPORT_SCHEMA: Dict[str, type] = {
    "date": str,
    "ticket_id": str,
    "issue_type": str,
    "resolution_hours": float,
    "satisfaction_score": float,
    "churn_risk": str,
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


def _clean_finance(df: pd.DataFrame) -> pd.DataFrame:
    """
    Nettoie et type le dataset finance.

    Conversions :
        - date          -> datetime64[ns]
        - revenue       -> float64
        - cost          -> float64
        - profit        -> float64
        - growth_rate   -> float64

    Args:
        df: DataFrame brut.

    Returns:
        DataFrame nettoyé et typé.
    """
    df = df.copy()
    df.columns = df.columns.str.strip().str.lower()

    # Parsing des dates
    df["date"] = pd.to_datetime(df["date"], format="%Y-%m-%d", errors="coerce")

    # Colonnes numériques
    for col in ["revenue", "cost", "profit", "growth_rate"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # Suppression des lignes sans date valide (clé primaire)
    nb_invalid_dates = int(df["date"].isna().sum())
    if nb_invalid_dates > 0:
        logger.warning("[finance] %d lignes avec date invalide supprimées", nb_invalid_dates)
        df = df.dropna(subset=["date"])

    # Remplacement des valeurs numériques nulles par la médiane
    for col in ["revenue", "cost", "profit", "growth_rate"]:
        nb_nulls = int(df[col].isna().sum())
        if nb_nulls > 0:
            median_val = df[col].median()
            df[col] = df[col].fillna(median_val)
            logger.warning(
                "[finance] %d valeurs nulles dans '%s' remplacées par la médiane (%.2f)",
                nb_nulls, col, median_val,
            )

    df = df.sort_values("date").reset_index(drop=True)
    logger.info("[finance] Nettoyage terminé — %d lignes", len(df))
    return df


def _clean_marketing(df: pd.DataFrame) -> pd.DataFrame:
    """
    Nettoie et type le dataset marketing.

    Conversions :
        - date            -> datetime64[ns]
        - campaign_id     -> str
        - channel         -> str (strip, lower)
        - budget          -> float64
        - clicks          -> Int64 (nullable integer)
        - conversions     -> Int64 (nullable integer)
        - conversion_rate -> float64

    Args:
        df: DataFrame brut.

    Returns:
        DataFrame nettoyé et typé.
    """
    df = df.copy()
    df.columns = df.columns.str.strip().str.lower()

    # Parsing des dates
    df["date"] = pd.to_datetime(df["date"], format="%Y-%m-%d", errors="coerce")

    # Colonnes texte
    df["campaign_id"] = df["campaign_id"].astype(str).str.strip()
    df["channel"] = df["channel"].astype(str).str.strip().str.lower()

    # Colonnes numériques flottantes
    for col in ["budget", "conversion_rate"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # Colonnes entières
    for col in ["clicks", "conversions"]:
        df[col] = pd.to_numeric(df[col], errors="coerce").round().astype("Int64")

    # Suppression des lignes sans date valide
    nb_invalid_dates = int(df["date"].isna().sum())
    if nb_invalid_dates > 0:
        logger.warning("[marketing] %d lignes avec date invalide supprimées", nb_invalid_dates)
        df = df.dropna(subset=["date"])

    # Gestion des valeurs nulles numériques
    for col in ["budget", "conversion_rate"]:
        nb_nulls = int(df[col].isna().sum())
        if nb_nulls > 0:
            median_val = df[col].median()
            df[col] = df[col].fillna(median_val)
            logger.warning(
                "[marketing] %d valeurs nulles dans '%s' remplacées par la médiane (%.2f)",
                nb_nulls, col, median_val,
            )

    for col in ["clicks", "conversions"]:
        nb_nulls = int(df[col].isna().sum())
        if nb_nulls > 0:
            median_val = int(df[col].median())
            df[col] = df[col].fillna(median_val)
            logger.warning(
                "[marketing] %d valeurs nulles dans '%s' remplacées par la médiane (%d)",
                nb_nulls, col, median_val,
            )

    df = df.sort_values("date").reset_index(drop=True)
    logger.info("[marketing] Nettoyage terminé — %d lignes", len(df))
    return df


def _clean_support(df: pd.DataFrame) -> pd.DataFrame:
    """
    Nettoie et type le dataset support client.

    Conversions :
        - date               -> datetime64[ns]
        - ticket_id          -> str
        - issue_type         -> str (strip, lower)
        - resolution_hours   -> float64
        - satisfaction_score -> float64  (valeurs valides : 1.0 – 5.0)
        - churn_risk         -> str (strip, lower) valeurs : low | medium | high

    Args:
        df: DataFrame brut.

    Returns:
        DataFrame nettoyé et typé.
    """
    df = df.copy()
    df.columns = df.columns.str.strip().str.lower()

    # Parsing des dates
    df["date"] = pd.to_datetime(df["date"], format="%Y-%m-%d", errors="coerce")

    # Colonnes texte
    df["ticket_id"] = df["ticket_id"].astype(str).str.strip()
    df["issue_type"] = df["issue_type"].astype(str).str.strip().str.lower()
    df["churn_risk"] = df["churn_risk"].astype(str).str.strip().str.lower()

    # Colonnes numériques
    for col in ["resolution_hours", "satisfaction_score"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # Validation du score de satisfaction (1-5)
    invalid_scores = df["satisfaction_score"].notna() & (
        (df["satisfaction_score"] < 1.0) | (df["satisfaction_score"] > 5.0)
    )
    nb_invalid = int(invalid_scores.sum())
    if nb_invalid > 0:
        logger.warning(
            "[support] %d scores de satisfaction hors de [1, 5] mis à NaN", nb_invalid
        )
        df.loc[invalid_scores, "satisfaction_score"] = float("nan")

    # Validation des valeurs churn_risk
    valid_churn = {"low", "medium", "high"}
    invalid_churn = ~df["churn_risk"].isin(valid_churn)
    nb_invalid_churn = int(invalid_churn.sum())
    if nb_invalid_churn > 0:
        logger.warning(
            "[support] %d valeurs 'churn_risk' invalides remplacées par 'medium'",
            nb_invalid_churn,
        )
        df.loc[invalid_churn, "churn_risk"] = "medium"

    # Suppression des lignes sans date valide
    nb_invalid_dates = int(df["date"].isna().sum())
    if nb_invalid_dates > 0:
        logger.warning("[support] %d lignes avec date invalide supprimées", nb_invalid_dates)
        df = df.dropna(subset=["date"])

    # Gestion des valeurs nulles numériques
    for col in ["resolution_hours", "satisfaction_score"]:
        nb_nulls = int(df[col].isna().sum())
        if nb_nulls > 0:
            median_val = df[col].median()
            df[col] = df[col].fillna(median_val)
            logger.warning(
                "[support] %d valeurs nulles dans '%s' remplacées par la médiane (%.2f)",
                nb_nulls, col, median_val,
            )

    df = df.sort_values("date").reset_index(drop=True)
    logger.info("[support] Nettoyage terminé — %d lignes", len(df))
    return df


# ============================================================
# Fonction principale
# ============================================================

def load_datasets(data_dir: Optional[Path] = None) -> Dict[str, pd.DataFrame]:
    """
    Charge, valide et nettoie les trois datasets CSV du projet.

    Les fichiers attendus dans data_dir :
        - 01_finance_performance.csv
        - 02_marketing_campaigns.csv
        - 03_customer_support.csv

    Args:
        data_dir: Répertoire contenant les CSV.
                  Si None, utilise DATA_DIR défini dans config.py.

    Returns:
        dict avec les clés "finance", "marketing", "support"
        et les DataFrames nettoyés comme valeurs.

    Raises:
        FileNotFoundError: Si un fichier CSV est introuvable.
        ValueError:        Si un dataset ne contient pas les colonnes attendues.
    """
    if data_dir is not None:
        resolved_dir = Path(data_dir)
        finance_path = resolved_dir / FINANCE_CSV.name
        marketing_path = resolved_dir / MARKETING_CSV.name
        support_path = resolved_dir / SUPPORT_CSV.name
    else:
        resolved_dir = DATA_DIR
        finance_path = FINANCE_CSV
        marketing_path = MARKETING_CSV
        support_path = SUPPORT_CSV

    logger.info("Chargement des datasets depuis : %s", resolved_dir)

    datasets: Dict[str, pd.DataFrame] = {}

    # ---- Finance ----
    if not finance_path.exists():
        raise FileNotFoundError(f"Fichier introuvable : {finance_path}")
    logger.info("Chargement du fichier finance : %s", finance_path)
    df_finance = pd.read_csv(finance_path)
    _validate_columns(df_finance, FINANCE_SCHEMA, "finance")
    datasets["finance"] = _clean_finance(df_finance)

    # ---- Marketing ----
    if not marketing_path.exists():
        raise FileNotFoundError(f"Fichier introuvable : {marketing_path}")
    logger.info("Chargement du fichier marketing : %s", marketing_path)
    df_marketing = pd.read_csv(marketing_path)
    _validate_columns(df_marketing, MARKETING_SCHEMA, "marketing")
    datasets["marketing"] = _clean_marketing(df_marketing)

    # ---- Support ----
    if not support_path.exists():
        raise FileNotFoundError(f"Fichier introuvable : {support_path}")
    logger.info("Chargement du fichier support : %s", support_path)
    df_support = pd.read_csv(support_path)
    _validate_columns(df_support, SUPPORT_SCHEMA, "support")
    datasets["support"] = _clean_support(df_support)

    logger.info(
        "Datasets chargés avec succès — finance: %d lignes | marketing: %d lignes | support: %d lignes",
        len(datasets["finance"]),
        len(datasets["marketing"]),
        len(datasets["support"]),
    )
    return datasets


def _detect_dataset_type(columns: pd.Index) -> str:
    """
    Détecte le type de dataset à partir des colonnes.

    Args:
        columns: Colonnes du CSV.

    Returns:
        "finance", "marketing", "support" ou "unknown".
    """
    normalized = {str(col).strip().lower() for col in columns}

    schemas = {
        "finance": set(FINANCE_SCHEMA.keys()),
        "marketing": set(MARKETING_SCHEMA.keys()),
        "support": set(SUPPORT_SCHEMA.keys()),
    }

    best_type = "unknown"
    best_ratio = 0.0

    for dataset_type, expected_columns in schemas.items():
        ratio = len(normalized & expected_columns) / len(expected_columns)
        if ratio > best_ratio:
            best_ratio = ratio
            best_type = dataset_type

    return best_type if best_ratio >= 0.7 else "unknown"


def _find_uploaded_dataset_paths(upload_dir: Path) -> Dict[str, Path]:
    """
    Trouve les fichiers uploadés et les mappe vers finance/marketing/support.

    Si plusieurs fichiers matchent le même type, le plus récent est conservé.

    Args:
        upload_dir: Dossier des uploads.

    Returns:
        Mapping {"finance": Path, "marketing": Path, "support": Path}.
    """
    selected: Dict[str, Path] = {}
    selected_mtime: Dict[str, float] = {}

    for csv_path in upload_dir.glob("*.csv"):
        try:
            preview_df = pd.read_csv(csv_path, nrows=5)
            dataset_type = _detect_dataset_type(preview_df.columns)
            if dataset_type == "unknown":
                continue

            mtime = csv_path.stat().st_mtime
            current = selected_mtime.get(dataset_type, float("-inf"))
            if mtime >= current:
                selected[dataset_type] = csv_path
                selected_mtime[dataset_type] = mtime

        except Exception as e:
            logger.warning("Impossible d'analyser le fichier uploadé %s: %s", csv_path, e)

    return selected


def load_uploaded_datasets(upload_dir: Optional[Path] = None) -> Dict[str, pd.DataFrame]:
    """
    Charge, valide et nettoie les datasets depuis le dossier uploads.

    Args:
        upload_dir: Dossier des fichiers uploadés. Si None, utilise UPLOADS_DIR.

    Returns:
        dict avec les clés "finance", "marketing", "support".

    Raises:
        FileNotFoundError: Si un des trois datasets est introuvable dans uploads.
        ValueError: Si un fichier trouvé ne respecte pas le schéma attendu.
    """
    from backend.config import UPLOADS_DIR

    resolved_dir = Path(upload_dir) if upload_dir is not None else UPLOADS_DIR
    logger.info("Chargement des datasets uploadés depuis : %s", resolved_dir)

    if not resolved_dir.exists():
        raise FileNotFoundError(f"Dossier uploads introuvable : {resolved_dir}")

    mapped_paths = _find_uploaded_dataset_paths(resolved_dir)
    missing_types = {"finance", "marketing", "support"} - set(mapped_paths.keys())
    if missing_types:
        raise FileNotFoundError(
            "Fichiers uploadés manquants pour : "
            f"{', '.join(sorted(missing_types))}. "
            "Uploadez un CSV pour chaque domaine."
        )

    datasets: Dict[str, pd.DataFrame] = {}

    finance_path = mapped_paths["finance"]
    marketing_path = mapped_paths["marketing"]
    support_path = mapped_paths["support"]

    logger.info("Fichier finance uploadé sélectionné : %s", finance_path.name)
    logger.info("Fichier marketing uploadé sélectionné : %s", marketing_path.name)
    logger.info("Fichier support uploadé sélectionné : %s", support_path.name)

    df_finance = pd.read_csv(finance_path)
    _validate_columns(df_finance, FINANCE_SCHEMA, "finance")
    datasets["finance"] = _clean_finance(df_finance)

    df_marketing = pd.read_csv(marketing_path)
    _validate_columns(df_marketing, MARKETING_SCHEMA, "marketing")
    datasets["marketing"] = _clean_marketing(df_marketing)

    df_support = pd.read_csv(support_path)
    _validate_columns(df_support, SUPPORT_SCHEMA, "support")
    datasets["support"] = _clean_support(df_support)

    return datasets


# ============================================================
# Exécution directe — affichage debug
# ============================================================

if __name__ == "__main__":
    try:
        # Priorité : data/ si les fichiers y sont, sinon tunisia_datasets/
        alt_data_dir = Path(__file__).resolve().parents[2] / "tunisia_datasets"
        use_alt = not FINANCE_CSV.exists() and alt_data_dir.exists()

        logger.info(
            "=== Mode debug — répertoire : %s ===",
            alt_data_dir if use_alt else DATA_DIR,
        )
        datasets = load_datasets(alt_data_dir if use_alt else None)

        labels = {
            "finance": "01_finance_performance.csv",
            "marketing": "02_marketing_campaigns.csv",
            "support": "03_customer_support.csv",
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
