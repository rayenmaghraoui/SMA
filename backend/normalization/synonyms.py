"""
Dictionnaires de synonymes pour le mapping sémantique.

Ces dictionnaires constituent la première ligne de défense déterministe
du SchemaMapper, avant les méthodes basées sur les embeddings ou le LLM.

Couverture :
    - synonymes français et anglais
    - variations orthographiques courantes
    - abréviations métier (CA, CA_Total, panier_moyen, ...)
    - termes spécifiques au domaine retail tunisien

Maintenance :
    Ajouter de nouveaux synonymes en respectant la convention :
        - clés en lowercase, sans accent, sans espaces (utiliser _)
        - une liste de variantes pour chaque concept
"""

from __future__ import annotations

from typing import Dict, FrozenSet

from backend.normalization.schemas import CanonicalConcept


# ============================================================
# Dictionnaire principal : concept canonique → liste de synonymes
# ============================================================
#
# Les synonymes sont normalisés au moment de la comparaison
# (str.lower().strip().replace(" ", "_").replace("-", "_")).
# Pas besoin de gérer manuellement les variantes typographiques.


CONCEPT_SYNONYMS: Dict[CanonicalConcept, FrozenSet[str]] = {

    # ------------------------------------------------------------------
    # IDENTIFIANTS
    # ------------------------------------------------------------------

    CanonicalConcept.INVOICE_ID: frozenset({
        "invoice_id", "invoice", "facture", "facture_id", "id_facture",
        "num_facture", "numero_facture", "numero", "ref_facture",
        "reference", "transaction_id", "order_id", "commande_id",
        "id_commande", "id_transaction",
    }),

    CanonicalConcept.CUSTOMER_ID: frozenset({
        "customer_id", "client_id", "id_client", "customer", "client",
        "cust_id", "user_id", "id_user", "id_utilisateur",
    }),

    CanonicalConcept.PRODUCT_ID: frozenset({
        "product_id", "produit_id", "id_produit", "sku", "ref_produit",
        "product_ref", "reference_produit", "article_id",
    }),

    # ------------------------------------------------------------------
    # MONTANTS FINANCIERS
    # ------------------------------------------------------------------

    CanonicalConcept.REVENUE: frozenset({
        # FR
        "revenu", "revenus", "revenue", "revenue_tnd", "ca", "ca_total",
        "chiffre_affaires", "chiffre_d_affaires", "chiffres_affaires",
        "montant", "montant_total", "montant_ttc", "montant_ht",
        "total_ventes", "ventes_total", "ventes",
        # EN
        "sales", "turnover", "income", "gross_revenue", "total_revenue",
        "total_sales", "net_revenue", "amount", "total_amount",
        "gross_sales",
    }),

    CanonicalConcept.PROFIT: frozenset({
        # FR
        "profit", "profit_total", "profit_tnd", "estimated_profit",
        "benefice", "benefice_net", "benefices", "marge", "marge_brute",
        "marge_nette", "gain", "gains",
        # EN
        "net_income", "net_profit", "gross_profit", "earnings",
        "margin", "net_margin", "gross_margin", "operating_profit",
    }),

    CanonicalConcept.COST: frozenset({
        # FR
        "cout", "couts", "depense", "depenses", "charge", "charges",
        "frais", "cost_tnd", "cout_total",
        # EN
        "cost", "costs", "expenses", "expense", "operational_cost",
        "operating_cost", "total_cost", "cogs", "opex",
    }),

    CanonicalConcept.UNIT_PRICE: frozenset({
        # FR
        "prix_unitaire", "prix_u", "prix", "unit_price_tnd",
        "prix_vente_unitaire", "tarif_unitaire", "tarif",
        # EN
        "unit_price", "price_per_unit", "price", "selling_price",
    }),

    CanonicalConcept.AVG_PRICE: frozenset({
        # FR
        "prix_moyen", "prix_moy", "moyenne_prix", "tarif_moyen",
        # EN
        "average_price", "avg_price", "mean_price",
    }),

    CanonicalConcept.AVG_BASKET: frozenset({
        # FR
        "panier_moyen", "panier_moy", "ticket_moyen", "valeur_panier",
        "moyenne_panier",
        # EN
        "avg_basket", "average_basket", "basket_size", "average_order_value",
        "aov", "avg_order_value", "mean_basket",
    }),

    CanonicalConcept.PROFIT_MARGIN: frozenset({
        # FR
        "marge_pct", "marge_pourcentage", "marge_beneficiaire",
        "taux_marge", "marge_beneficiaire_pct",
        # EN
        "profit_margin", "profit_margin_pct", "margin_pct",
        "margin_percentage", "net_margin_pct", "gross_margin_pct",
    }),

    CanonicalConcept.GROWTH_RATE: frozenset({
        # FR
        "taux_croissance", "croissance", "evolution", "variation",
        "evolution_pct", "variation_pct",
        # EN
        "growth_rate", "growth", "growth_pct", "yoy_growth", "mom_growth",
    }),

    # ------------------------------------------------------------------
    # VOLUMES
    # ------------------------------------------------------------------

    CanonicalConcept.QUANTITY: frozenset({
        # FR
        "quantite", "quantites", "qte", "nb_unites", "unites",
        "nombre_unites", "qty",
        # EN
        "quantity", "qty", "units", "count", "num_units",
    }),

    CanonicalConcept.TOTAL_QUANTITY: frozenset({
        # FR
        "quantite_vendue", "quantites_vendues", "qte_vendue",
        "total_quantite", "volume_ventes", "volume_total",
        # EN
        "total_quantity", "total_qty", "quantity_sold", "qty_sold",
        "total_units_sold", "units_sold",
    }),

    CanonicalConcept.NB_TRANSACTIONS: frozenset({
        # FR
        "nb_transactions", "nombre_transactions", "transactions",
        "nb_commandes", "nb_ventes", "nombre_ventes", "nombre_factures",
        "nb_factures",
        # EN
        "transactions", "num_transactions", "transaction_count",
        "nb_orders", "num_orders", "order_count", "total_transactions",
    }),

    CanonicalConcept.NB_CUSTOMERS: frozenset({
        # FR
        "nb_clients", "nb_clients_uniques", "clients_uniques",
        "nombre_clients", "nombre_clients_uniques",
        # EN
        "num_customers", "customer_count", "unique_customers",
        "nb_users", "active_customers",
    }),

    # ------------------------------------------------------------------
    # DIMENSIONS
    # ------------------------------------------------------------------

    CanonicalConcept.PRODUCT_NAME: frozenset({
        # FR
        "produit", "nom_produit", "article", "nom_article",
        "designation", "designation_produit", "libelle_produit",
        # EN
        "product_name", "product", "item", "item_name", "article_name",
        "sku_name",
    }),

    CanonicalConcept.CATEGORY: frozenset({
        # FR
        "categorie", "categories", "gamme", "famille_produit",
        "type_produit", "rayon",
        # EN
        "category", "categories", "product_category", "product_type",
        "department", "segment",
    }),

    CanonicalConcept.REGION: frozenset({
        # FR
        "region", "regions", "customer_region", "region_client",
        "gouvernorat", "ville", "localite", "zone", "zone_geographique",
        "wilaya",
        # EN
        "region", "regions", "location", "area", "zone", "city",
        "governorate", "state", "province",
    }),

    CanonicalConcept.SALES_CHANNEL: frozenset({
        # FR
        "canal", "canaux", "sales_channel", "canal_vente", "canal_distribution",
        "circuit_distribution", "type_vente",
        # EN
        "channel", "channels", "sales_channel", "distribution_channel",
        "sales_channel_name",
    }),

    CanonicalConcept.PAYMENT_METHOD: frozenset({
        # FR
        "moyen_paiement", "methode_paiement", "type_paiement",
        "mode_paiement", "paiement",
        # EN
        "payment_method", "payment_type", "payment", "payment_mode",
    }),

    # ------------------------------------------------------------------
    # TEMPS
    # ------------------------------------------------------------------

    CanonicalConcept.DATE: frozenset({
        # FR
        "date", "date_vente", "sale_date", "date_facture", "date_commande",
        "date_transaction", "periode", "mois", "annee", "jour",
        # EN
        "date", "sale_date", "order_date", "transaction_date",
        "invoice_date", "period", "month", "year", "day", "timestamp",
    }),

    # ------------------------------------------------------------------
    # FORMAT CLÉ-VALEUR (KPIs globaux)
    # ------------------------------------------------------------------

    CanonicalConcept.INDICATOR_NAME: frozenset({
        "indicateur", "indicateurs", "kpi", "kpi_name", "metric",
        "nom_kpi", "nom_indicateur", "label", "metric_name",
    }),

    CanonicalConcept.INDICATOR_VALUE: frozenset({
        "valeur", "valeurs", "value", "kpi_value", "metric_value",
        "montant", "donnee", "resultat",
    }),

    # ------------------------------------------------------------------
    # MARKETING / CAMPAGNES
    # ------------------------------------------------------------------

    CanonicalConcept.CAMPAIGN_ID: frozenset({
        "campaign_id", "campagne", "id_campagne", "campagne_id",
        "campaign", "campaign_name", "nom_campagne",
    }),

    CanonicalConcept.BUDGET: frozenset({
        # FR
        "budget", "budget_tnd", "budget_total", "depense_marketing",
        "enveloppe", "cout_marketing",
        # EN
        "budget", "marketing_budget", "spend", "ad_spend",
    }),

    CanonicalConcept.CLICKS: frozenset({
        "clicks", "clics", "nb_clics", "nombre_clics", "click_count",
        "total_clicks",
    }),

    CanonicalConcept.CONVERSIONS: frozenset({
        "conversions", "nb_conversions", "nombre_conversions",
        "total_conversions", "conversion_count",
    }),

    CanonicalConcept.CONVERSION_RATE: frozenset({
        # FR
        "taux_conversion", "tx_conversion", "conversion_pct",
        # EN
        "conversion_rate", "cr", "conversion_pct", "cvr",
    }),

    # ------------------------------------------------------------------
    # SUPPORT / SATISFACTION
    # ------------------------------------------------------------------

    CanonicalConcept.TICKET_ID: frozenset({
        "ticket_id", "ticket", "id_ticket", "ticket_num", "case_id",
    }),

    CanonicalConcept.ISSUE_TYPE: frozenset({
        "issue_type", "type_probleme", "categorie_probleme",
        "type_ticket", "issue", "issue_category",
    }),

    CanonicalConcept.RESOLUTION_HOURS: frozenset({
        "resolution_hours", "temps_resolution", "duree_resolution",
        "resolution_time", "time_to_resolve",
    }),

    CanonicalConcept.SATISFACTION_SCORE: frozenset({
        "satisfaction_score", "score_satisfaction", "satisfaction",
        "csat", "nps", "rating", "customer_rating",
    }),

    CanonicalConcept.CHURN_RISK: frozenset({
        "churn_risk", "risque_churn", "risque_attrition", "churn",
        "attrition_risk",
    }),
}


# ============================================================
# Mots-clés par domaine métier (pour BusinessDomainDetector)
# ============================================================


DOMAIN_KEYWORDS: Dict[str, FrozenSet[str]] = {

    "finance": frozenset({
        "revenue", "profit", "cost", "margin", "ebitda", "cashflow",
        "ca", "chiffre_affaires", "benefice", "marge", "depense",
        "budget", "tresorerie", "compte_resultat", "bilan",
    }),

    "marketing": frozenset({
        "campaign", "campagne", "channel", "canal", "clicks", "clics",
        "conversion", "ctr", "cpc", "roi", "ad_spend",
        "social_media", "email", "seo", "sem",
    }),

    "sales": frozenset({
        "invoice", "facture", "order", "commande", "transaction",
        "product_name", "unit_price", "quantity", "qty", "sku",
        "sale_date", "customer", "client",
    }),

    "product": frozenset({
        "product", "produit", "category", "categorie", "sku",
        "inventory", "stock", "variant", "gamme",
        "quantite_vendue", "prix_moyen",
    }),

    "regional": frozenset({
        "region", "city", "ville", "country", "state", "province",
        "gouvernorat", "wilaya", "zone", "location", "area",
    }),

    "support": frozenset({
        "ticket", "issue", "resolution", "satisfaction", "csat",
        "nps", "churn", "complaint", "agent", "sla",
    }),

    "logistics": frozenset({
        "shipment", "livraison", "delivery", "warehouse", "stock",
        "inventory", "transit", "freight", "logistics",
        "supply_chain", "lead_time",
    }),

    "hr": frozenset({
        "employee", "employee_id", "salary", "salaire", "department",
        "departement", "headcount", "absenteeism", "tenure",
        "hire_date", "termination_date",
    }),
}


# ============================================================
# Index inversé : nom normalisé → concept canonique
# ============================================================
#
# Permet une lookup O(1) pour le matching exact / par synonyme.
# Calculé une seule fois à l'import du module.


def _build_reverse_index() -> Dict[str, CanonicalConcept]:
    """Construit l'index inversé synonyme → concept."""
    index: Dict[str, CanonicalConcept] = {}
    for concept, synonyms in CONCEPT_SYNONYMS.items():
        for synonym in synonyms:
            normalized = _normalize_term(synonym)
            # Le premier concept gagne en cas de collision (rare en pratique)
            if normalized not in index:
                index[normalized] = concept
    return index


def _normalize_term(term: str) -> str:
    """
    Normalise un terme pour matching insensible aux variantes typographiques.

    Transformations :
        - lowercase
        - strip
        - espaces et tirets → underscores
        - suppression des accents simples

    Args:
        term: Terme brut.

    Returns:
        Terme normalisé.
    """
    if not term:
        return ""

    normalized = term.strip().lower()
    normalized = normalized.replace(" ", "_").replace("-", "_")

    # Suppression des accents les plus courants en français
    replacements = {
        "à": "a", "â": "a", "ä": "a",
        "é": "e", "è": "e", "ê": "e", "ë": "e",
        "î": "i", "ï": "i",
        "ô": "o", "ö": "o",
        "ù": "u", "û": "u", "ü": "u",
        "ç": "c",
    }
    for accented, plain in replacements.items():
        normalized = normalized.replace(accented, plain)

    return normalized


# Index inversé pré-calculé (singleton effectif)
SYNONYM_INDEX: Dict[str, CanonicalConcept] = _build_reverse_index()


def find_concept_by_synonym(column_name: str) -> CanonicalConcept | None:
    """
    Cherche un concept canonique correspondant exactement au nom de colonne.

    Cette fonction est la première étape (déterministe, O(1)) du pipeline
    de mapping. Si elle retourne None, on passe à la similarité sémantique.

    Args:
        column_name: Nom de colonne brut.

    Returns:
        CanonicalConcept correspondant, ou None si aucun synonyme exact.
    """
    normalized = _normalize_term(column_name)
    return SYNONYM_INDEX.get(normalized)
