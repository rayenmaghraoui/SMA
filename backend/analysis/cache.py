"""
Cache d'analyse — évite de recalculer les KPIs si les CSV n'ont pas changé.

Stratégie :
    - Hash MD5 basé sur le nom + mtime + taille de chaque CSV dans uploads/
    - Si le hash correspond au cache sauvegardé, retourner les résultats en cache
    - Si les CSV ont changé, invalider le cache et lancer le pipeline complet
"""

import hashlib
import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional

from backend.config import DATA_DIR, UPLOADS_DIR

logger = logging.getLogger(__name__)

CACHE_FILE = DATA_DIR / "analysis_cache.json"


def _compute_uploads_hash() -> str:
    """Calcule un hash MD5 sur les CSV présents dans uploads/ (nom + mtime + taille)."""
    h = hashlib.md5()
    csv_files = sorted(UPLOADS_DIR.glob("*.csv"))
    if not csv_files:
        return ""
    for f in csv_files:
        stat = f.stat()
        h.update(f.name.encode())
        h.update(str(stat.st_mtime).encode())
        h.update(str(stat.st_size).encode())
    return h.hexdigest()


def get_cached_result() -> Optional[Dict[str, Any]]:
    """
    Retourne le résultat mis en cache si les CSV n'ont pas changé.

    Returns:
        Dict avec kpis, anomalies et report si cache valide, None sinon.
    """
    try:
        if not CACHE_FILE.exists():
            return None
        cache = json.loads(CACHE_FILE.read_text(encoding="utf-8"))
        current_hash = _compute_uploads_hash()
        if not current_hash or cache.get("hash") != current_hash:
            logger.info("[Cache] Hash différent — cache invalidé")
            return None
        logger.info("[Cache] Hit — résultats chargés depuis le cache")
        return cache
    except Exception as e:
        logger.warning("[Cache] Lecture échouée : %s", e)
        return None


def save_to_cache(state: Dict[str, Any]) -> None:
    """
    Sauvegarde le résultat d'une analyse dans le cache.

    On stocke le rapport complet (qui contient les kpis au format
    indicateurs attendu par le Dashboard) plutôt que les kpis bruts
    du pipeline, afin que les hits de cache retournent les bonnes données.

    Args:
        state: État final du pipeline (kpis, anomalies, report).
    """
    try:
        current_hash = _compute_uploads_hash()
        if not current_hash:
            return
        report = state.get("report", {})
        # kpis formatés (avec indicateurs) = report.kpis ; fallback = kpis bruts
        formatted_kpis = report.get("kpis", {}) if report else state.get("kpis", {})
        cache = {
            "hash": current_hash,
            "kpis": formatted_kpis,
            "anomalies": state.get("anomalies", []),
            "report": report,
        }
        CACHE_FILE.write_text(
            json.dumps(cache, ensure_ascii=False, default=str),
            encoding="utf-8",
        )
        logger.info("[Cache] Résultats sauvegardés (hash=%s)", current_hash[:8])
    except Exception as e:
        logger.warning("[Cache] Écriture échouée : %s", e)


def invalidate_cache() -> None:
    """Supprime le fichier de cache (appeler après un upload de nouveaux CSV)."""
    try:
        if CACHE_FILE.exists():
            CACHE_FILE.unlink()
            logger.info("[Cache] Cache invalidé suite à un upload")
    except Exception as e:
        logger.warning("[Cache] Invalidation échouée : %s", e)
