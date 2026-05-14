# Plan du Mémoire PFE — Niveau Master
## "Système Multi-Agents d'Aide à la Décision pour PME Tunisiennes"
### Méthodologie : CRISP-DM (data science) × SCRUM (gestion de projet)

---

> **Note encadrant :** Ce plan intègre deux méthodologies de façon complémentaire et non redondante :
> - **SCRUM** structure la conduite du projet (sprints, backlog, livrables incrémentaux)
> - **CRISP-DM** structure la démarche data science (compréhension → préparation → modélisation → évaluation → déploiement)
> - Le chapitre de réalisation (Chapitre 5) fusionne les deux : chaque sprint est ancré dans une phase CRISP-DM.

## Page de garde
- Titre du sujet
- Etudiant
- Encadrant académique
- Encadrant entreprise
- Etablissement / Année universitaire

## Remerciements

## Résumé
- Résumé en français (10-15 lignes)
- Mots-clés (5 à 8 mots)

## Abstract
- Résumé en anglais
- Keywords

## Table des matières

## Liste des figures

## Liste des tableaux

## Liste des abréviations
- IA, KPI, API, RAG, SSE, ROI, SLA, etc.

---

# Chapitre 1: Introduction Générale

## 1.1 Contexte du projet
Présenter le contexte stage/entreprise, la problématique de pilotage des performances, et le besoin d'une aide à la décision basée sur les données.

## 1.2 Problématique
Expliquer les difficultés rencontrées:
- Données dispersées et peu exploitées
- Difficulté à transformer les KPIs en décisions concrètes
- Manque de recommandations priorisées

## 1.3 Objectif général
Concevoir une plateforme intelligente multi-agents capable de:
- analyser les données opérationnelles,
- détecter les anomalies,
- interpréter les résultats,
- proposer des recommandations stratégiques,
- générer un rapport décisionnel.

## 1.4 Objectifs spécifiques
- Mettre en place un pipeline séquentiel de 5 agents
- Intégrer un backend API et un frontend web
- Ajouter une couche RAG pour enrichir les recommandations
- Proposer une interface chat avec streaming

## 1.5 Méthodologie adoptée
Ce projet suit une approche **AGILE SCRUM** pour l'organisation du travail, avec des itérations courtes et des incréments fonctionnels à chaque sprint.

Formulation recommandée:
> "Le projet a été conduit selon AGILE SCRUM, avec planification incrémentale, revues régulières et amélioration continue, tout en s'appuyant sur une logique CRISP-DM adaptée pour la partie traitement de données."

## 1.6 Structure du mémoire
Décrire brièvement le contenu de chaque chapitre.

---

# Chapitre 2: Etat de l'art et concepts

## 2.1 Aide à la décision et Business Intelligence
## 2.2 Intelligence artificielle générative en entreprise
## 2.3 Systèmes multi-agents
## 2.4 RAG (Retrieval-Augmented Generation)
## 2.5 Méthodologie AGILE SCRUM
- Rôles: Product Owner, Scrum Master, Development Team
- Artefacts: Product Backlog, Sprint Backlog, Increment
- Cérémonies: Sprint Planning, Daily Scrum, Sprint Review, Sprint Retrospective

---

# Chapitre 3: Analyse des besoins et planification SCRUM

## 3.1 Recueil des besoins
### 3.1.1 Besoins fonctionnels
- Upload de fichiers CSV
- Analyse des données
- Chat décisionnel
- Génération et consultation de rapports

### 3.1.2 Besoins non fonctionnels
- Performance
- Fiabilité
- Lisibilité de l'interface
- Maintenabilité

## 3.2 User stories (exemples)
- En tant que manager, je veux charger mes fichiers pour lancer une analyse personnalisée.
- En tant que décideur, je veux visualiser les KPI pour évaluer la performance globale.
- En tant qu'utilisateur, je veux obtenir des recommandations priorisées pour agir rapidement.

## 3.3 Product Backlog (exemple)
- US1: Upload et validation CSV
- US2: Calcul des KPI par domaine
- US3: Détection d'anomalies
- US4: Interprétation IA
- US5: RAG contextuel
- US6: Recommandations priorisées
- US7: Génération de rapport
- US8: Interface chat SSE

## 3.4 Plan des sprints
Durée recommandée: 1 à 2 semaines par sprint.

---

# Chapitre 4: Conception et architecture

## 4.1 Architecture globale
- Frontend React
- Backend FastAPI
- Pipeline multi-agents LangGraph
- RAG avec ChromaDB et embeddings
- LLM local via Ollama

## 4.2 Flux de données
Input CSV -> Analysis Agent -> Interpretation Agent -> RAG Agent -> Recommendation Agent -> Report Agent -> Résultat final.

## 4.3 Modélisation
- Schéma des données
- Etat partagé entre agents
- Schéma des routes API

---

# Chapitre 5: Réalisation par Sprints (AGILE SCRUM)

## Sprint 0: Cadrage et initialisation
### Objectif
Préparer l'environnement, clarifier le périmètre, définir le backlog.

### Travaux réalisés
- Installation des outils
- Initialisation du projet (backend/frontend)
- Définition des user stories et priorités

### Livrables
- Product Backlog initial
- Architecture cible validée

### Ce que tu présentes au jury
- Vision produit
- Choix méthodologique SCRUM
- Macro planning des sprints

---

## Sprint 1: Ingestion et préparation des données
### Objectif
Permettre le chargement, la validation et le nettoyage des datasets.

### Travaux réalisés
### Travaux réalisés
- Loader des CSV (adapté au nouveau format : 5 fichiers en `data/uploads/`)
- Validation des schémas et mapping vers les tables attendues (ventes, régions, catégories, canaux, kpis globaux)
- Nettoyage, normalisation et contrôle de qualité des données (types, dates, valeurs manquantes)

### Livrables
- Module data prêt
- Jeux de données exploitables

### Ce que tu présentes
- Qualité des données
- Règles de validation
- Gestion des erreurs

---

## Sprint 2: Agent d'analyse (KPI + anomalies)
### Objectif
Produire des indicateurs métier et détecter les anomalies.

### Travaux réalisés
- Analyse finance, canaux de vente, catégories produits
- Détection anomalies (IQR)

### Livrables
- KPIs par domaine
- Liste d'anomalies explicites

### Ce que tu présentes
- Formules KPI
- Méthode de détection
- Pertinence métier des résultats

---

## Sprint 3: Orchestration multi-agents
### Objectif
Mettre en place le pipeline séquentiel des 5 agents.

### Travaux réalisés
- Etat partagé des agents
- Graphe d'exécution LangGraph
- Gestion des transitions

### Livrables
- Pipeline exécutable de bout en bout

### Ce que tu présentes
- Pourquoi multi-agents au lieu d'un seul agent
- Flux séquentiel et responsabilités de chaque agent

---

## Sprint 4: Interprétation IA + RAG
### Objectif
Enrichir l'analyse par un raisonnement IA contextualisé.

### Travaux réalisés
- Intégration LLM (Ollama/Mistral)
- Ingestion documents métier
- Recherche sémantique avec ChromaDB

### Livrables
- Interprétation textuelle
- Contexte documentaire pertinent

### Ce que tu présentes
- Principe du RAG
- Qualité des réponses avec et sans contexte

---

## Sprint 5: Recommandations + rapport final
### Objectif
Transformer l'analyse en recommandations actionnables.

### Travaux réalisés
- Agent de recommandation
- Priorisation des actions
- Agent de génération de rapport

### Livrables
- Rapport structuré
- Recommandations priorisées

### Ce que tu présentes
- Valeur décisionnelle
- Structure du rapport final

---

## Sprint 6: API et interface utilisateur
### Objectif
Rendre la solution utilisable via web app complète.

### Travaux réalisés
- Routes API (analyze, upload, chat, report)
- Frontend dashboard/chat/upload/report
- Streaming SSE sur le chat

### Livrables
- Application full-stack utilisable

### Ce que tu présentes
- Parcours utilisateur complet
- Démo live: upload -> analyse -> recommandations -> rapport

---

## Sprint 7: Tests, stabilisation et documentation
### Objectif
Fiabiliser la solution et finaliser les livrables PFE.

### Travaux réalisés
- Tests unitaires et d'intégration
- Correction de bugs
- Rédaction documentation technique

### Livrables
- Version stable
- Documentation finale

### Ce que tu présentes
- Stratégie de test
- Limites actuelles
- Pistes d'amélioration

---

# Chapitre 6: Technologies utilisées

## 6.1 Backend
- Python
- FastAPI
- Uvicorn
- Pydantic

## 6.2 Pipeline IA
- LangGraph (orchestration des agents)
- LangChain (intégration LLM/RAG)
- DeepSeek-V3.2 via Azure AI Foundry (génération de texte)

## 6.3 Analyse de données
- Pandas
- NumPy
- Scikit-learn

## 6.4 RAG
- ChromaDB (base vectorielle)
- Sentence Transformers (embeddings)
- Documents métier indexés

## 6.5 Frontend
- React
- Vite
- Tailwind CSS
- Framer Motion
- Recharts
- Axios

## 6.6 Outils qualité et dev
- Git/GitHub
- Pytest
- ESLint
- Environnement virtuel Python (.venv)

---

# Chapitre 7: Tests et validation

## 7.1 Stratégie de test
- Tests unitaires backend
- Tests des routes API
- Tests du pipeline d'agents

## 7.2 Scénarios de validation
- Cas nominal
- Cas d'erreurs (fichiers invalides, LLM indisponible)
- Vérification de cohérence des recommandations

## 7.3 Résultats
- Qualité des sorties
- Robustesse globale

---

# Chapitre 8: Bilan, limites et perspectives

## 8.1 Bilan
- Objectifs atteints
- Apports techniques et métier

## 8.2 Limites
- Dépendance qualité des données
- Variabilité des réponses LLM
- Pas de MLOps complet

## 8.3 Perspectives
- Authentification et gestion multi-utilisateur
- Historique et comparaison multi-périodes
- Alertes intelligentes
- Déploiement cloud et CI/CD

---

# Conclusion générale
- Synthèse du travail réalisé
- Réponse à la problématique
- Contribution du projet

---

# Annexes
- Exemples de datasets
- Extraits de code clés
- Captures d'écran de l'application
- Product backlog détaillé
- Planning réel des sprints

## Annexes — Exemples de datasets (détail)

Les jeux de données utilisés dans le projet sont placés dans `data/uploads/` et comprennent 5 fichiers principaux :

| Fichier | Colonnes principales | Usage |
|--------:|---------------------|-------|
| `01_donnees_vente.csv` | invoice_id, product_name, category, quantity, unit_price_tnd, revenue_tnd, customer_id, customer_region, sale_date, sales_channel, payment_method, estimated_profit | Analyse produits, top produits, meilleure région, meilleur canal |
| `02_analyse_region.csv` | customer_region, ca_total, profit_total, nb_transactions, panier_moyen | CA par région, top région, panier moyen régional |
| `03_analyse_categorie.csv` | category, ca_total, profit_total, nb_transactions, quantite_vendue, prix_moyen | Segmentation par catégorie, top catégorie CA/quantité |
| `04_analyse_canaux.csv` | sales_channel, ca_total, nb_transactions, panier_moyen | Performance par canal, meilleur canal, panier moyen canal |
| `05_kpis_globaux.csv` | indicateur, valeur | KPIs agrégés : revenue_total, profit_total, profit_margin, nb_transactions, nb_clients |

Ces cinq fichiers couvrent toutes les dimensions de l'analyse : performance globale, détail des ventes, analyse régionale, catégories de produits et canaux de distribution.

---

# Conseils de rédaction par sprint (ce qu'il faut raconter)

Pour chaque sprint dans ton rapport, respecte ce mini-format:
1. **Objectif du sprint** (ce qu'on veut livrer)
2. **Backlog sélectionné** (US prises)
3. **Conception/choix techniques**
4. **Implémentation réalisée**
5. **Difficultés rencontrées + solutions**
6. **Résultat / incrément livré**
7. **Leçons apprises (rétrospective)**

Ce format montre clairement l'application de SCRUM au jury.

---

# Exemple de tableau SCRUM à insérer

| Sprint | Objectif | User Stories | Livrable | Statut |
|---|---|---|---|---|
| Sprint 1 | Préparer les données | US1 | Loader + validation CSV | Terminé |
| Sprint 2 | Produire KPI | US2, US3 | Agent d'analyse | Terminé |
| Sprint 3 | Orchestrer les agents | US4 | Graphe multi-agents | Terminé |
| Sprint 4 | Ajouter intelligence contextuelle | US5 | RAG + interprétation | Terminé |
| Sprint 5 | Recommandations + rapport | US6, US7 | Rapport final | Terminé |
| Sprint 6 | Construire interface | US8 | App web complète | Terminé |
| Sprint 7 | Stabiliser | QA | Tests + doc | Terminé |

---

# Formulation finale recommandée (à copier)

"Le projet a été réalisé selon la méthodologie AGILE SCRUM, avec une organisation en sprints incrémentaux. Chaque sprint a produit un incrément fonctionnel validé en revue. Cette approche a permis d'assurer une progression continue, une meilleure gestion des priorités métier, et une adaptation rapide aux retours de l'encadrement et de l'entreprise d'accueil."