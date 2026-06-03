"""
Schémas internes standardisés — contrats des analyzers existants.

Ce module définit les concepts canoniques (CanonicalConcept) et les schémas
attendus par chaque analyzer. C'est le contrat que la couche de normalisation
doit satisfaire pour préserver la compatibilité avec les analyzers.

Les analyzers existants (kpis_analyzer, canaux_analyzer, categories_analyzer,
plus les analyses inline ventes et regions) restent strictement inchangés.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, FrozenSet, List, Optional


# ============================================================
# Domaines métier supportés
# ============================================================


class BusinessDomain(str, Enum):
    """
    Domaines métier détectables par BusinessDomainDetector.

    Ces domaines correspondent aux analyzers disponibles dans le projet.
    Le domaine "unknown" est retourné quand aucune classification fiable
    n'est possible (utilisé pour déclencher un fallback LLM si activé).
    """

    FINANCE = "finance"
    MARKETING = "marketing"
    SALES = "sales"
    PRODUCT = "product"
    REGIONAL = "regional"
    SUPPORT = "support"
    LOGISTICS = "logistics"
    HR = "hr"
    UNKNOWN = "unknown"


# ============================================================
# Concepts canoniques (vocabulaire interne unifié)
# ============================================================


class CanonicalConcept(str, Enum):
    """
    Concepts canoniques utilisés en interne par les analyzers.

    Chaque concept représente une notion métier unique vers laquelle
    les colonnes hétérogènes des datasets uploadés doivent être mappées.

    Convention : nom en snake_case, en anglais (consistant avec le code).
    """

    # ----- Identifiants -----
    INVOICE_ID = "invoice_id"
    CUSTOMER_ID = "customer_id"
    PRODUCT_ID = "product_id"

    # ----- Montants financiers (en TND) -----
    REVENUE = "revenue_tnd"              # Chiffre d'affaires
    PROFIT = "profit_tnd"                # Bénéfice / marge
    COST = "cost_tnd"                    # Coût / dépense
    UNIT_PRICE = "unit_price_tnd"        # Prix unitaire
    AVG_PRICE = "avg_price_tnd"          # Prix moyen
    AVG_BASKET = "avg_basket_tnd"        # Panier moyen
    PROFIT_MARGIN = "profit_margin_pct"  # Marge bénéficiaire %
    GROWTH_RATE = "growth_rate_pct"      # Taux de croissance %

    # ----- Volumes -----
    QUANTITY = "quantity"                # Quantité par ligne
    TOTAL_QUANTITY = "total_quantity"    # Quantité agrégée
    NB_TRANSACTIONS = "nb_transactions"  # Nombre de transactions
    NB_CUSTOMERS = "nb_customers"        # Nombre de clients uniques

    # ----- Dimensions -----
    PRODUCT_NAME = "product_name"
    CATEGORY = "category"
    REGION = "region"
    SALES_CHANNEL = "sales_channel"
    PAYMENT_METHOD = "payment_method"

    # ----- Temps -----
    DATE = "date"                        # Date de transaction / période

    # ----- Format clé-valeur -----
    INDICATOR_NAME = "indicator_name"    # Nom de l'indicateur (KPI)
    INDICATOR_VALUE = "indicator_value"  # Valeur de l'indicateur

    # ----- Marketing / Campagnes -----
    CAMPAIGN_ID = "campaign_id"
    BUDGET = "budget_tnd"
    CLICKS = "clicks"
    CONVERSIONS = "conversions"
    CONVERSION_RATE = "conversion_rate_pct"

    # ----- Support / Satisfaction -----
    TICKET_ID = "ticket_id"
    ISSUE_TYPE = "issue_type"
    RESOLUTION_HOURS = "resolution_hours"
    SATISFACTION_SCORE = "satisfaction_score"
    CHURN_RISK = "churn_risk"


# ============================================================
# Mapping concept canonique → nom de colonne attendu par l'analyzer
# ============================================================
#
# Les analyzers utilisent des noms de colonnes français (issus du CSV
# original). Pour préserver la compatibilité sans modifier le code des
# analyzers, on définit ici la projection inverse :
#       concept canonique → nom exact attendu en sortie.


_CONCEPT_TO_LEGACY_COLUMN: Dict[CanonicalConcept, str] = {
    # Ventes (analyse inline _analyze_ventes)
    CanonicalConcept.INVOICE_ID:      "invoice_id",
    CanonicalConcept.PRODUCT_NAME:    "product_name",
    CanonicalConcept.CATEGORY:        "category",
    CanonicalConcept.QUANTITY:        "quantity",
    CanonicalConcept.UNIT_PRICE:      "unit_price_tnd",
    CanonicalConcept.REVENUE:         "revenue_tnd",
    CanonicalConcept.CUSTOMER_ID:     "customer_id",
    CanonicalConcept.REGION:          "customer_region",
    CanonicalConcept.DATE:            "sale_date",
    CanonicalConcept.SALES_CHANNEL:   "sales_channel",
    CanonicalConcept.PAYMENT_METHOD:  "payment_method",
    CanonicalConcept.PROFIT:          "estimated_profit",

    # Agrégations régionales / canaux / catégories
    CanonicalConcept.AVG_BASKET:       "panier_moyen",
    CanonicalConcept.NB_TRANSACTIONS:  "nb_transactions",
    CanonicalConcept.TOTAL_QUANTITY:   "quantite_vendue",
    CanonicalConcept.AVG_PRICE:        "prix_moyen",

    # KPIs globaux (format clé-valeur)
    CanonicalConcept.INDICATOR_NAME:  "indicateur",
    CanonicalConcept.INDICATOR_VALUE: "valeur",
}


def get_legacy_column_name(concept: CanonicalConcept) -> str:
    """
    Retourne le nom de colonne attendu par les analyzers pour un concept.

    Si aucun mapping legacy n'existe (concept récent), retourne la valeur
    de l'enum elle-même (snake_case en anglais).

    Args:
        concept: Concept canonique.

    Returns:
        Nom de colonne à utiliser dans le DataFrame normalisé.
    """
    return _CONCEPT_TO_LEGACY_COLUMN.get(concept, concept.value)


# ============================================================
# Schémas internes standardisés par analyzer
# ============================================================


@dataclass(frozen=True)
class InternalSchema:
    """
    Contrat d'entrée d'un analyzer.

    Définit les concepts canoniques requis (obligatoires) et optionnels
    qu'un dataset doit fournir après normalisation pour être analysable.

    Attributes:
        name:               Identifiant de l'analyzer cible.
        domain:             Domaine métier associé.
        required_concepts:  Concepts obligatoires (ValueError si manquants).
        optional_concepts:  Concepts utilisés si présents.
        description:        Description humaine du schéma.
    """

    name: str
    domain: BusinessDomain
    required_concepts: FrozenSet[CanonicalConcept]
    optional_concepts: FrozenSet[CanonicalConcept] = field(default_factory=frozenset)
    description: str = ""

    @property
    def all_concepts(self) -> FrozenSet[CanonicalConcept]:
        """Tous les concepts (requis + optionnels)."""
        return self.required_concepts | self.optional_concepts

    @property
    def required_columns(self) -> List[str]:
        """Noms de colonnes legacy correspondant aux concepts requis."""
        return [get_legacy_column_name(c) for c in self.required_concepts]


# ----- Schéma : analyses inline ventes (analysis_agent._analyze_ventes) -----

VENTES_SCHEMA = InternalSchema(
    name="ventes",
    domain=BusinessDomain.SALES,
    required_concepts=frozenset({
        CanonicalConcept.REVENUE,
        CanonicalConcept.QUANTITY,
        CanonicalConcept.PRODUCT_NAME,
        CanonicalConcept.REGION,
        CanonicalConcept.SALES_CHANNEL,
    }),
    optional_concepts=frozenset({
        CanonicalConcept.INVOICE_ID,
        CanonicalConcept.CATEGORY,
        CanonicalConcept.CUSTOMER_ID,
        CanonicalConcept.DATE,
        CanonicalConcept.PAYMENT_METHOD,
        CanonicalConcept.UNIT_PRICE,
        CanonicalConcept.PROFIT,
    }),
    description="Dataset transactionnel — 1 ligne par facture.",
)


# ----- Schéma : analyses inline regions (analysis_agent._analyze_regions) -----

REGIONS_SCHEMA = InternalSchema(
    name="regions",
    domain=BusinessDomain.REGIONAL,
    required_concepts=frozenset({
        CanonicalConcept.REGION,
        CanonicalConcept.REVENUE,
        CanonicalConcept.NB_TRANSACTIONS,
        CanonicalConcept.AVG_BASKET,
    }),
    optional_concepts=frozenset({
        CanonicalConcept.PROFIT,
    }),
    description="Agrégation des ventes par région géographique.",
)


# ----- Schéma : canaux_analyzer -----
#
# Note : canaux_analyzer attend explicitement "ca_total" et non "revenue_tnd".
# On ajoute ce mapping spécifique au transformer pour ce schéma.

CANAUX_SCHEMA = InternalSchema(
    name="canaux",
    domain=BusinessDomain.MARKETING,
    required_concepts=frozenset({
        CanonicalConcept.SALES_CHANNEL,
        CanonicalConcept.REVENUE,            # → ca_total
        CanonicalConcept.NB_TRANSACTIONS,
        CanonicalConcept.AVG_BASKET,
    }),
    description="Performance des canaux de vente / distribution.",
)


# ----- Schéma : categories_analyzer -----

CATEGORIES_SCHEMA = InternalSchema(
    name="categories",
    domain=BusinessDomain.PRODUCT,
    required_concepts=frozenset({
        CanonicalConcept.CATEGORY,
        CanonicalConcept.REVENUE,            # → ca_total
        CanonicalConcept.PROFIT,             # → profit_total
        CanonicalConcept.NB_TRANSACTIONS,
        CanonicalConcept.TOTAL_QUANTITY,
        CanonicalConcept.AVG_PRICE,
    }),
    description="Performance des catégories de produits.",
)


# ----- Schéma : kpis_analyzer (format clé-valeur) -----

KPIS_SCHEMA = InternalSchema(
    name="kpis",
    domain=BusinessDomain.FINANCE,
    required_concepts=frozenset({
        CanonicalConcept.INDICATOR_NAME,
        CanonicalConcept.INDICATOR_VALUE,
    }),
    description="KPIs globaux au format clé-valeur (indicateur / valeur).",
)


# ============================================================
# Surcharges de mapping legacy par schéma
# ============================================================
#
# Certains analyzers attendent des noms de colonnes spécifiques qui
# diffèrent du nom legacy par défaut du concept. Par exemple :
#       canaux_analyzer attend "ca_total" pour CanonicalConcept.REVENUE
#       categories_analyzer attend "ca_total" et "profit_total" aggrégés


_SCHEMA_LEGACY_OVERRIDES: Dict[str, Dict[CanonicalConcept, str]] = {
    "canaux": {
        CanonicalConcept.REVENUE: "ca_total",
    },
    "categories": {
        CanonicalConcept.REVENUE: "ca_total",
        CanonicalConcept.PROFIT: "profit_total",
    },
    "regions": {
        CanonicalConcept.REVENUE: "ca_total",
        CanonicalConcept.PROFIT: "profit_total",
    },
}


def get_column_for_schema(schema_name: str, concept: CanonicalConcept) -> str:
    """
    Retourne le nom de colonne à utiliser pour un concept dans un schéma donné.

    Priorité : override schéma-spécifique → mapping legacy global → valeur enum.

    Args:
        schema_name: Nom du schéma ("canaux", "categories", "regions", ...).
        concept:     Concept canonique.

    Returns:
        Nom de colonne attendu par l'analyzer cible.
    """
    overrides = _SCHEMA_LEGACY_OVERRIDES.get(schema_name, {})
    if concept in overrides:
        return overrides[concept]
    return get_legacy_column_name(concept)


# ============================================================
# Registre des schémas
# ============================================================


_SCHEMA_REGISTRY: Dict[str, InternalSchema] = {
    VENTES_SCHEMA.name:     VENTES_SCHEMA,
    REGIONS_SCHEMA.name:    REGIONS_SCHEMA,
    CANAUX_SCHEMA.name:     CANAUX_SCHEMA,
    CATEGORIES_SCHEMA.name: CATEGORIES_SCHEMA,
    KPIS_SCHEMA.name:       KPIS_SCHEMA,
}


_DOMAIN_TO_SCHEMAS: Dict[BusinessDomain, List[InternalSchema]] = {
    BusinessDomain.SALES:     [VENTES_SCHEMA],
    BusinessDomain.REGIONAL:  [REGIONS_SCHEMA],
    BusinessDomain.MARKETING: [CANAUX_SCHEMA],
    BusinessDomain.PRODUCT:   [CATEGORIES_SCHEMA],
    BusinessDomain.FINANCE:   [KPIS_SCHEMA],
}


def get_all_schemas() -> List[InternalSchema]:
    """Retourne tous les schémas enregistrés."""
    return list(_SCHEMA_REGISTRY.values())


def get_schema_by_name(name: str) -> Optional[InternalSchema]:
    """
    Récupère un schéma par son nom.

    Args:
        name: Nom du schéma (ex: "ventes", "kpis").

    Returns:
        InternalSchema ou None si le nom est inconnu.
    """
    return _SCHEMA_REGISTRY.get(name)


def get_schema_for_domain(domain: BusinessDomain) -> List[InternalSchema]:
    """
    Retourne les schémas associés à un domaine métier.

    Args:
        domain: Domaine métier détecté.

    Returns:
        Liste des schémas compatibles (vide si domaine sans schéma associé).
    """
    return _DOMAIN_TO_SCHEMAS.get(domain, [])
