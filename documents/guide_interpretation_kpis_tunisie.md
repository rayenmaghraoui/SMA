# Guide d'Interprétation des KPIs et de l'Analyse de Données
## Cadre de référence pour l'évaluation des performances des PME

**Date de rédaction :** Mars 2026
**Public cible :** Dirigeants, Data Analysts, Agents IA 
**Objectif :** Fournir les clés d'interprétation des seuils critiques et des benchmarks afin d'analyser les données (Finances, Marketing, RH, Support) et de diagnostiquer la santé de l'entreprise.

---

## 1. Principes de l'Analyse des KPIs

Un indicateur clé de performance (Key Performance Indicator - KPI) n'a de valeur que s'il est contextualisé. Pour l'IA, il faut toujours comparer une valeur à son "Seuil critique" ou à la "Norme du secteur".

**Méthode de Diagnostic :**
1. **Valeur constatée :** Lecture dans le dataset.
2. **Évaluation :** "Bon" / "Acceptable" / "Critique" en fonction des seuils de référence.
3. **Recommandation :** L'action corrective à déclencher si le seuil est critique.

---

## 2. KPIs Financiers (Finance & Comptabilité)

| KPI | Formule / Définition | Norme / Objectif | Seuil Critique (Alerte) | Interprétation et Action |
|---|---|---|---|---|
| **Marge Brute globale** | (CA - Coût d'achat) / CA | 30% - 40% (Commerce) <br> 50%+ (Services) | < 25% | **Alerte.** L'entreprise vend trop peu cher ou achète trop cher. Augmenter les prix ou changer de fournisseur. |
| **Marge Nette** | Résultat Net / CA | 8% - 15% | < 3% | **Alerte forte.** L'entreprise a trop de charges fixes. Procéder à un audit de réduction des coûts (loyers, charges indirectes). |
| **Délai Moyen de Recouvrement (DSO)** | (Créances clients / CA TTC) * 365 | 30 à 45 jours | > 90 jours | **Alerte trésorerie.** En Tunisie, c'est grave. Risque d'insolvabilité. Lancer des recouvrements stricts, bloquer les livraisons aux clients mauvais payeurs. |
| **Ratio de Liquidité** | Actif courant / Passif courant | > 1.2 | < 1.0 | **Alerte.** L'entreprise ne peut pas payer ses dettes à court terme. Cesser les investissements inutiles, reporter les dettes avec banques/fournisseurs. |

---

## 3. KPIs Marketing et Vente

| KPI | Formule / Définition | Norme / Objectif | Seuil Critique (Alerte) | Interprétation et Action |
|---|---|---|---|---|
| **Coût d'Acquisition Client (CAC)** | Budget Mkt & Vente / Nouveaux Clients | Dépend du produit. Marge sur 1 achat > CAC. | CAC > Marge générée | **Alerte.** Les campagnes coûtent plus cher que ce que le client rapporte. Couper les campagnes non rentables, revoir le ciblage Facebook Ads. |
| **Taux de Conversion** | (Achats / Visiteurs) * 100 | 1.5% - 3% (E-com) | < 0.5% | **Alerte.** Le trafic vient mais n'achète pas. Revoir le site web, les prix, la clarté de l'offre. |
| **Taux d'Attrition (Churn Rate)** | Clients perdus / Clients totaux | 2% - 5% par mois (SaaS/Abo) | > 10% par mois | **Alerte majeure.** Les clients partent en masse (problème produit caché ou SAV médiocre). Lancer un questionnaire d'urgence aux clients déçus. |
| **Retour sur Investissement (ROAS)** | CA de la campagne / Coût campagne | > 300% (soit x3) | < 100% (soit x1) | **Critique.** L'argent de la publicité est perdu. Arrêter les pubs. |

---

## 4. KPIs Service Client (Customer Support)

L'impact du service client est souvent sous-estimé, mais il dirige la réputation de l'entreprise (et donc son churn).

| KPI | Formule / Définition | Norme / Objectif | Seuil Critique (Alerte) | Interprétation et Action |
|---|---|---|---|---|
| **Temps de Première Réponse (FRT)** | Temps moyen pour répondre au 1er ticket | < 2 heures | > 24 heures | **Alerte.** Les clients attendent trop longtemps. Installer un chatbot pour les questions de base, embaucher du staff support. |
| **CSAT (Customer Satisfaction Score)** | % de notes positives ("Bon" / "Très bon") | > 85% | < 70% | **Alerte qualité.** Le service est déceptif. Former les agents, analyser les motifs de mécontentement via les commentaires. |
| **Taux de Résolution au Premier Appel (FCR)** | Tickets résolus en 1 contact / Total tickets | > 75% | < 50% | **Vigilance.** Les agents manquent d'autonomie ou le produit est trop complexe. Créer une base de connaissances interne. |

---

## 5. KPIs Ressources Humaines (RH)

| KPI | Formule / Définition | Norme / Objectif | Seuil Critique (Alerte) | Interprétation et Action |
|---|---|---|---|---|
| **Taux de Turnover** | Départs / Effectif moyen | 5% - 10% par an | > 20% par an | **Alerte climat social.** Quelque chose ne va pas (salaire, management toxique). Lancer des entretiens de sortie (exit interviews). |
| **Taux d'Absentéisme** | Heures absences / Heures théoriques | < 3% | > 8% | **Alerte désengagement.** Instaurer un contrôle (contre-visites médicales si abus), revoir les conditions de travail (prime de présentéisme). |
| **Coût du Turnover** | Recrutement + formation d'un remplaçant | N/A | Trop élevé comparé au salaire | Investir dans des de primes de rétention (loyalty bonus) coûte souvent moins cher que de remplacer les employés formés. |

---

## 6. Méthodologie du "Diagnostic IA" pour les Datasets CSV

Lorsqu'un Agent (Data Analysis Agent) analyse un jeu de données (ex: `01_finance_performance.csv`), il doit suivre cette logique :

1. **Extraction de la moyenne, médiane et tendance** de la colonne analysée (ex: CA par mois).
2. **Identification des anomalies (Outliers)** ou des tendances baissières consécutives (3 mois de baisse actent une crise).
3. **Application de la matrice ci-dessus** : Comparer le seuil réel au "Seuil Critique".
4. Si le seuil critique est dépassé, **l'agent doit formuler un Diagnostic structuré** :
   - *Observation :* "Le DSO est de 115 jours en Q3."
   - *Interprétation :* "Ceci est bien supérieur au seuil critique de 90 jours."
   - *Recommandation métiers :* "Il est urgent de mettre en place une politique d'escompte pour paiement anticipé et de renforcer le département recouvrement des créances."

---

> **Ce document fait partie de la base de connaissances du système AI Business Consultant. Il donne le référentiel chiffré permettant au LLM et aux agents d'interpréter intelligemment les données quantitatives brutes des PME.**
