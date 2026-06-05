"""
Analyseur avancé — prévisions de ventes (forecasting) et comparaison de périodes.

Ce module exploite le dataset des transactions individuelles (01_donnees_vente.csv)
pour produire deux analyses orientées aide à la décision :

    1. Prévision des ventes futures via régression linéaire (scikit-learn),
       à partir de la série temporelle agrégée par mois.
    2. Comparaison de deux périodes (KPIs, évolution en pourcentage,
       répartition par catégorie).
"""

import logging
from typing import Any, Dict, Optional

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression

logger = logging.getLogger(__name__)


# ============================================================
# Prévision des ventes (forecasting) — agrégation mensuelle
# ============================================================

def forecast_sales(
    df_ventes: pd.DataFrame,
    horizon: int = 3,
    seasonal: bool = True,
) -> Dict[str, Any]:
    """
    Prévoit le chiffre d'affaires des prochains mois.

    La méthode applique une décomposition additive simple :
        CA(t) = tendance(t) + saisonnalité(mois) + résidu

    La tendance est estimée par régression linéaire (scikit-learn) sur l'index
    temporel. La composante saisonnière correspond à l'écart moyen, désaisonnalisé
    de la tendance, observé pour chaque mois calendaire (janvier à décembre) —
    elle capture par exemple la hausse des ventes en fin d'année. La prévision de
    chaque mois futur additionne la tendance projetée et l'indice saisonnier
    correspondant. Un intervalle de confiance (±1 écart-type des résidus
    désaisonnalisés) encadre chaque prévision.

    Args:
        df_ventes: DataFrame des transactions (colonnes sale_date, revenue_tnd).
        horizon:   Nombre de mois futurs à prévoir (défaut 3).
        seasonal:  Active la composante saisonnière mensuelle (défaut True).

    Returns:
        Dictionnaire contenant l'historique, les prévisions et les métadonnées.

    Raises:
        ValueError: Si les colonnes requises sont absentes ou l'historique
                    est insuffisant (moins de 3 mois).
    """
    logger.info("Prévision des ventes — horizon=%d mois, saisonnalité=%s", horizon, seasonal)

    required = {"sale_date", "revenue_tnd"}
    missing = required - set(df_ventes.columns)
    if missing:
        raise ValueError(f"Colonnes manquantes pour la prévision : {missing}")

    df = df_ventes.copy()
    df["sale_date"] = pd.to_datetime(df["sale_date"], errors="coerce")
    df = df.dropna(subset=["sale_date"])

    if df.empty:
        raise ValueError("Aucune transaction valide avec une date exploitable.")

    # Agrégation mensuelle du chiffre d'affaires
    series = (
        df.set_index("sale_date")["revenue_tnd"]
        .resample("MS")  # Month Start
        .sum()
        .sort_index()
    )

    if len(series) < 3:
        raise ValueError(
            "Historique insuffisant pour une prévision fiable (minimum 3 mois)."
        )

    # ── Étape 1 : tendance par régression linéaire ──
    x = np.arange(len(series)).reshape(-1, 1)
    y = series.values.astype(float)

    model = LinearRegression()
    model.fit(x, y)
    trend_fit = model.predict(x)

    # ── Étape 2 : composante saisonnière mensuelle ──
    # Indice saisonnier = écart moyen à la tendance pour chaque mois calendaire.
    seasonal_index: Dict[int, float] = {m: 0.0 for m in range(1, 13)}
    if seasonal and len(series) >= 12:
        detrended = pd.Series(y - trend_fit, index=series.index)
        month_means = detrended.groupby(detrended.index.month).mean()
        # Centrage : la somme des indices saisonniers doit être nulle (additif pur)
        center = float(month_means.mean())
        seasonal_index = {
            int(m): round(float(v - center), 2) for m, v in month_means.items()
        }

    # ── Étape 3 : résidus désaisonnalisés → intervalle de confiance ──
    season_hist = np.array([seasonal_index.get(d.month, 0.0) for d in series.index])
    residuals = y - trend_fit - season_hist
    std_resid = float(np.std(residuals))

    # ── Étape 4 : projection des mois futurs ──
    future_x = np.arange(len(series), len(series) + horizon).reshape(-1, 1)
    future_trend = model.predict(future_x)
    future_dates = pd.date_range(
        start=series.index[-1] + pd.DateOffset(months=1),
        periods=horizon,
        freq="MS",
    )
    future_y = np.array(
        [t + seasonal_index.get(d.month, 0.0) for t, d in zip(future_trend, future_dates)]
    )

    history = [
        {"date": d.strftime("%Y-%m"), "revenue": round(float(v), 2), "type": "historique"}
        for d, v in series.items()
    ]

    forecast = [
        {
            "date": d.strftime("%Y-%m"),
            "revenue": round(float(max(v, 0)), 2),
            "lower": round(float(max(v - std_resid, 0)), 2),
            "upper": round(float(max(v + std_resid, 0)), 2),
            "type": "prévision",
        }
        for d, v in zip(future_dates, future_y)
    ]

    # ── Indicateurs de synthèse ──
    slope = float(model.coef_[0])
    trend = "croissance" if slope > 0 else ("déclin" if slope < 0 else "stable")
    total_forecast = round(float(sum(max(v, 0) for v in future_y)), 2)
    avg_historical = round(float(series.mean()), 2)
    # R² du modèle complet (tendance + saisonnalité) sur l'historique
    full_fit = trend_fit + season_hist
    ss_res = float(np.sum((y - full_fit) ** 2))
    ss_tot = float(np.sum((y - y.mean()) ** 2))
    r2 = round(1 - ss_res / ss_tot, 3) if ss_tot > 0 else 0.0

    # Mois le plus fort en saisonnalité (pour l'insight)
    peak_month = max(seasonal_index, key=seasonal_index.get) if any(seasonal_index.values()) else None
    month_names = {
        1: "janvier", 2: "février", 3: "mars", 4: "avril", 5: "mai", 6: "juin",
        7: "juillet", 8: "août", 9: "septembre", 10: "octobre", 11: "novembre", 12: "décembre",
    }

    logger.info(
        "Prévision calculée — tendance=%s, total prévu=%.0f TND, R²=%.2f, saisonnalité=%s",
        trend, total_forecast, r2, seasonal,
    )

    return {
        "history": history,
        "forecast": forecast,
        "metadata": {
            "trend": trend,
            "slope": round(slope, 2),
            "total_forecast": total_forecast,
            "avg_historical": avg_historical,
            "r2_score": r2,
            "horizon": horizon,
            "n_periods_history": len(series),
            "seasonal": seasonal,
            "peak_month": month_names.get(peak_month) if peak_month else None,
        },
    }


# ============================================================
# Comparaison de deux périodes
# ============================================================

def compare_periods(
    df_ventes: pd.DataFrame,
    period_a_start: str,
    period_a_end: str,
    period_b_start: str,
    period_b_end: str,
) -> Dict[str, Any]:
    """
    Compare les performances commerciales entre deux périodes.

    Args:
        df_ventes:      DataFrame des transactions.
        period_a_start: Date de début période A (format YYYY-MM-DD).
        period_a_end:   Date de fin période A.
        period_b_start: Date de début période B.
        period_b_end:   Date de fin période B.

    Returns:
        Dictionnaire avec les KPIs de chaque période, leur évolution
        en pourcentage et la répartition par catégorie.

    Raises:
        ValueError: Si les colonnes requises sont absentes ou une période
                    ne contient aucune transaction.
    """
    logger.info(
        "Comparaison de périodes — A=[%s→%s], B=[%s→%s]",
        period_a_start, period_a_end, period_b_start, period_b_end,
    )

    required = {"sale_date", "revenue_tnd", "estimated_profit", "category"}
    missing = required - set(df_ventes.columns)
    if missing:
        raise ValueError(f"Colonnes manquantes pour la comparaison : {missing}")

    df = df_ventes.copy()
    df["sale_date"] = pd.to_datetime(df["sale_date"], errors="coerce")
    df = df.dropna(subset=["sale_date"])

    def _slice(start: str, end: str) -> pd.DataFrame:
        mask = (df["sale_date"] >= pd.to_datetime(start)) & (
            df["sale_date"] <= pd.to_datetime(end)
        )
        return df.loc[mask]

    df_a = _slice(period_a_start, period_a_end)
    df_b = _slice(period_b_start, period_b_end)

    if df_a.empty or df_b.empty:
        raise ValueError(
            "Une des deux périodes ne contient aucune transaction. "
            "Vérifiez les dates sélectionnées."
        )

    def _kpis(d: pd.DataFrame) -> Dict[str, float]:
        ca = float(d["revenue_tnd"].sum())
        prof = float(d["estimated_profit"].sum())
        nb = int(len(d))
        return {
            "ca_total":        round(ca, 2),
            "profit_total":    round(prof, 2),
            "marge":           round((prof / ca * 100) if ca > 0 else 0.0, 2),
            "nb_transactions": nb,
            "panier_moyen":    round((ca / nb) if nb > 0 else 0.0, 2),
        }

    kpis_a = _kpis(df_a)
    kpis_b = _kpis(df_b)

    def _evolution(a: float, b: float) -> float:
        """Évolution en % de la période A vers la période B."""
        if a == 0:
            return 0.0
        return round((b - a) / abs(a) * 100, 2)

    evolution = {
        key: _evolution(kpis_a[key], kpis_b[key])
        for key in ["ca_total", "profit_total", "marge", "nb_transactions", "panier_moyen"]
    }

    # Répartition du CA par catégorie pour chaque période
    def _by_category(d: pd.DataFrame) -> Dict[str, float]:
        grp = d.groupby("category")["revenue_tnd"].sum()
        return {str(k): round(float(v), 2) for k, v in grp.items()}

    cat_a = _by_category(df_a)
    cat_b = _by_category(df_b)
    all_cats = sorted(set(cat_a) | set(cat_b))
    category_comparison = [
        {
            "category": cat,
            "period_a": cat_a.get(cat, 0.0),
            "period_b": cat_b.get(cat, 0.0),
        }
        for cat in all_cats
    ]

    logger.info(
        "Comparaison calculée — CA évolution=%.1f%%, profit évolution=%.1f%%",
        evolution["ca_total"], evolution["profit_total"],
    )

    return {
        "period_a": {"label": f"{period_a_start} → {period_a_end}", "kpis": kpis_a},
        "period_b": {"label": f"{period_b_start} → {period_b_end}", "kpis": kpis_b},
        "evolution": evolution,
        "category_comparison": category_comparison,
    }


# ============================================================
# Bornes de dates disponibles (pour pré-remplir l'interface)
# ============================================================

def get_date_range(df_ventes: pd.DataFrame) -> Dict[str, Optional[str]]:
    """
    Retourne la plage de dates disponible dans le dataset des ventes.

    Args:
        df_ventes: DataFrame des transactions.

    Returns:
        Dictionnaire {min_date, max_date} au format YYYY-MM-DD,
        ou None si aucune date exploitable.
    """
    if "sale_date" not in df_ventes.columns or df_ventes.empty:
        return {"min_date": None, "max_date": None}

    dates = pd.to_datetime(df_ventes["sale_date"], errors="coerce").dropna()
    if dates.empty:
        return {"min_date": None, "max_date": None}

    return {
        "min_date": dates.min().strftime("%Y-%m-%d"),
        "max_date": dates.max().strftime("%Y-%m-%d"),
    }