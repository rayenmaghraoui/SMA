# Rapport PFE Complet
## Système Multi-Agents d'Aide à la Décision d'Entreprise

## Résumé
Ce projet de fin d'études présente la conception et la réalisation d'une plateforme intelligente d'aide à la décision d'entreprise. La solution développée exploite une architecture web full-stack et un pipeline multi-agents pour transformer des données opérationnelles en recommandations stratégiques. Le système ingère des données financières, marketing et support client, calcule des indicateurs de performance (KPI), détecte des anomalies, enrichit l'analyse avec un mécanisme RAG, puis génère un rapport structuré pour la prise de décision.

La mise en oeuvre suit une méthodologie AGILE SCRUM avec des incréments fonctionnels à chaque sprint. Côté technique, le backend est construit avec FastAPI, le pipeline d'agents est orchestré avec LangGraph, l'analyse de données repose sur Pandas/Scikit-learn, le RAG s'appuie sur ChromaDB et sentence-transformers, et l'interface est développée avec React. Le modèle LLM utilisé est DeepSeek-V3.2, accessible via Azure AI Foundry.

Le résultat est une application capable de fournir des analyses claires, contextualisées et actionnables, avec une interface de chat en streaming et une restitution sous forme de rapport décisionnel.

Mots-clés: Multi-agents, Aide à la décision, IA, RAG, FastAPI, React, SCRUM, KPI

---

## Abstract
This final-year project presents the design and implementation of an intelligent decision-support platform for enterprises. The solution relies on a full-stack web architecture and a multi-agent pipeline to transform operational data into strategic recommendations. The system ingests financial, marketing, and customer support data, computes key performance indicators (KPIs), detects anomalies, enriches interpretation with a RAG mechanism, and generates a structured report for decision-making.

The implementation follows an AGILE SCRUM methodology with functional increments delivered at each sprint. On the technical side, the backend is built with FastAPI, the agent pipeline is orchestrated with LangGraph, data analysis is handled by Pandas/Scikit-learn, RAG relies on ChromaDB and sentence-transformers, and the UI is developed with React. The LLM used is DeepSeek-V3.2, accessed through Azure AI Foundry.

The final output is an application that provides clear, contextualized, and actionable analytics through a streaming chat interface and a decision-oriented report.

Keywords: Multi-agent systems, Decision support, AI, RAG, FastAPI, React, SCRUM, KPI

---

# Table des matières
1. Introduction générale
2. Contexte, problématique et objectifs
3. Méthodologie AGILE SCRUM
4. Etude et spécification des besoins
5. Conception et architecture de la solution
6. Réalisation technique
7. Déroulement par sprints
8. Validation, résultats et discussion
9. Limites et perspectives
10. Conclusion générale

---

# 1. Introduction générale

La transformation numérique des entreprises a conduit à une production massive de données opérationnelles. Malgré cette abondance, la capacité à convertir ces données en décisions concrètes demeure un défi majeur. Les responsables métiers disposent souvent de fichiers hétérogènes (finances, campagnes marketing, support client), mais manquent d'une vue intégrée, interprétable et orientée action.

Ce projet répond à cette problématique en proposant une plateforme intelligente d'aide à la décision. La solution combine l'analyse de données, les modèles de langage, et une architecture multi-agents pour automatiser le cycle complet: ingestion des données, extraction d'indicateurs, détection d'anomalies, interprétation métier, génération de recommandations, puis restitution sous forme de rapport.

L'objectif est de fournir un outil opérationnel, transparent et extensible, utilisable dans un cadre professionnel réel.

---

# 2. Contexte, problématique et objectifs

## 2.1 Contexte
Le projet a été réalisé dans le cadre d'un stage de fin d'études, avec un besoin concret exprimé autour du pilotage de la performance d'entreprise. L'attente principale est de disposer d'un assistant intelligent capable de réduire le temps d'analyse, d'augmenter la qualité des diagnostics, et de proposer des actions priorisées.

## 2.2 Problématique
La problématique peut être formulée ainsi:
Comment transformer automatiquement des données opérationnelles brutes en recommandations stratégiques fiables, lisibles et actionnables, au sein d'une application web intégrée?

Sous-problèmes:
- Données multi-domaines non consolidées.
- Interprétation métier dépendante d'expertise humaine.
- Difficulté à relier KPI, anomalies et plan d'action.
- Besoin d'un système explicable et évolutif.

## 2.3 Objectif général
Concevoir et implémenter une plateforme multi-agents d'aide à la décision qui orchestre automatiquement l'analyse, l'interprétation et la recommandation.

## 2.4 Objectifs spécifiques
- Développer un backend API robuste pour piloter le pipeline.
- Construire cinq agents spécialisés et complémentaires.
- Mettre en place un module RAG pour contextualiser les réponses.
- Fournir une interface web complète (dashboard, upload, chat, rapport).
- Structurer les résultats sous forme de rapport décisionnel.

## 2.5 Contributions
- Architecture modulaire full-stack.
- Pipeline séquentiel multi-agents en production locale.
- Couplage IA générative + RAG + analytics classiques.
- Expérience utilisateur interactive avec streaming SSE.

---

# 3. Méthodologie AGILE SCRUM

## 3.1 Choix méthodologique
Le projet est conduit selon AGILE SCRUM pour favoriser:
- l'incrémentation rapide,
- la priorisation continue,
- l'adaptation aux retours métier,
- la livraison progressive de valeur.

En parallèle, la logique de travail data suit une démarche proche de CRISP-DM (compréhension, préparation, modélisation, évaluation, déploiement).

## 3.2 Rôles SCRUM appliqués
- Product Owner (fonctionnel): représentation des besoins métier et priorisation backlog.
- Scrum Master (organisation): facilitation, suivi d'avancement, suppression des blocages.
- Development Team: conception, implémentation, tests et intégration.

## 3.3 Artefacts
- Product Backlog: liste priorisée des fonctionnalités (upload, KPI, anomalies, RAG, chat, rapport).
- Sprint Backlog: sous-ensemble d'items réalisés par itération.
- Increment: composant fonctionnel livrable à la fin de chaque sprint.

## 3.4 Cérémonies
- Sprint Planning: sélection des objectifs du sprint.
- Daily suivi: avancement, obstacles, plan du jour.
- Sprint Review: démonstration de l'incrément.
- Sprint Retrospective: amélioration continue du processus.

---

# 4. Etude et spécification des besoins

## 4.1 Besoins fonctionnels
- Charger des fichiers CSV d'entreprise.
- Lancer une analyse complète automatique.
- Poser des questions en langage naturel via chat.
- Visualiser KPI, anomalies et recommandations.
- Générer et consulter un rapport structuré.
- Vérifier l'état de santé de la plateforme.

## 4.2 Besoins non fonctionnels
- Performance acceptable sur machine locale.
- Disponibilité API et robustesse des routes.
- Réponses compréhensibles et bien structurées.
- Maintenabilité grâce à une architecture modulaire.
- Extensibilité pour ajouter nouveaux agents ou datasets.

## 4.3 User stories représentatives
- En tant que manager, je veux analyser rapidement mes données pour identifier les priorités.
- En tant que décideur, je veux des recommandations classées par priorité.
- En tant qu'utilisateur métier, je veux une interface claire pour suivre les résultats.

## 4.4 Critères d'acceptation principaux
- Le pipeline doit produire KPI + anomalies + rapport en une seule exécution.
- Le chat doit afficher une progression d'étapes et une réponse en streaming.
- Les erreurs doivent être capturées et remontées proprement.

---

# 5. Conception et architecture de la solution

## 5.1 Vue d'ensemble
L'architecture comprend quatre couches:
1. Interface utilisateur (React).
2. API backend (FastAPI).
3. Pipeline intelligent (LangGraph, 5 agents).
4. Services IA et données (LLM, RAG, analyse CSV).

## 5.2 Architecture logique
- Frontend consomme les endpoints REST et SSE.
- Backend orchestre le pipeline et centralise la logique métier.
- Agents échangent un état partagé unique.
- RAG enrichit l'interprétation et les recommandations.
- Rapport final persisté pour consultation ultérieure.

## 5.3 Etat partagé entre agents
L'état contient notamment:
- raw_data
- kpis
- anomalies
- interpretation
- rag_context
- recommendations
- report
- errors
- current_step

Ce design garantit la traçabilité de la donnée tout au long du pipeline.

## 5.4 Flux de données
Flux analyse:
1. Lecture/validation des datasets.
2. Calcul des KPI.
3. Détection des anomalies.
4. Interprétation LLM.
5. Recherche contextuelle RAG.
6. Recommandations priorisées.
7. Rapport final.

Flux chat:
1. Question utilisateur.
2. Exécution streaming du pipeline.
3. Emission d'événements step/token/report/done.

---

# 6. Réalisation technique

## 6.1 Backend API
Le backend expose des routes pour:
- analyse complète,
- upload des données,
- chat streaming et chat simple,
- récupération du rapport,
- santé système.

Points clés:
- CORS configuré pour le frontend.
- Health check avec test de disponibilité Azure AI Foundry.
- Modèles Pydantic pour validation des requêtes/réponses.

## 6.2 Pipeline multi-agents
Le pipeline est linéaire et déterministe:
Analysis Agent -> Interpretation Agent -> RAG Agent -> Recommendation Agent -> Report Agent.

### 6.2.1 Analysis Agent
Responsabilités:
- Charger datasets par défaut ou injectés.
- Calculer KPI finance/marketing/support.
- Détecter anomalies via IQR.

Sorties principales:
- kpis
- anomalies

### 6.2.2 Interpretation Agent
Responsabilités:
- Construire un prompt structuré à partir des KPI, anomalies et question utilisateur.
- Appeler le LLM pour produire une interprétation métier.
- Nettoyer les duplications textuelles éventuelles.

Sortie principale:
- interpretation

### 6.2.3 RAG Agent
Responsabilités:
- Construire des requêtes sémantiques ciblées selon les signaux détectés.
- Interroger la base ChromaDB.
- Retourner les passages les plus pertinents, sans doublons.

Sortie principale:
- rag_context

### 6.2.4 Recommendation Agent
Responsabilités:
- Générer des recommandations priorisées (format structuré).
- Exploiter interprétation + contexte RAG + KPI.
- Prévoir fallback robuste en cas d'échec parsing LLM.

Sortie principale:
- recommendations

### 6.2.5 Report Agent
Responsabilités:
- Construire un rapport JSON final homogène.
- Intégrer résumé exécutif, KPI formatés, anomalies, recommandations, sources.

Sortie principale:
- report

## 6.3 Analyse de données
### 6.3.1 Préparation
- Validation des schémas attendus.
- Conversion des types.
- Nettoyage des valeurs manquantes.
- Contrôles de cohérence par domaine.

### 6.3.2 KPI implémentés
Finance:
- revenu total, profit total, marge, croissance, tendance, volatilité.

Marketing:
- budget total, conversions, taux moyen, canal optimal, ROI par canal, coût/conversion.

Support:
- satisfaction moyenne, délai de résolution, taux churn élevé, conformité SLA, tendance satisfaction.

### 6.3.3 Détection d'anomalies
Méthode IQR:
- seuil bas: Q1 - 1.5 x IQR
- seuil haut: Q3 + 1.5 x IQR

## 6.4 RAG
### 6.4.1 Ingestion
- Chargement des documents métier.
- Découpage hybride (headers markdown puis recursive split).
- Indexation dans ChromaDB.

### 6.4.2 Recherche
- Similarité cosinus.
- Top-k configurable.
- Métadonnées source/section conservées.

## 6.5 Frontend
Pages principales:
- Dashboard: KPI, graphiques et actions de lancement.
- Upload: import et validation de fichiers.
- Chat: interface conversationnelle avec progression en temps réel.
- Report: restitution détaillée et impression.

Composants clés:
- Cartes KPI,
- Visualisations,
- Messages de chat,
- Suivi d'étapes agents.

## 6.6 Streaming SSE
Le chat utilise un flux événementiel:
- step: progression du pipeline,
- token: sortie textuelle progressive,
- report: objet rapport,
- done/error: clôture.

Ce choix améliore la perception de réactivité et la transparence du traitement.

---

# 7. Déroulement par sprints

## Sprint 0 - Cadrage et setup
Objectif:
- définir vision produit,
- préparer environnement,
- établir backlog initial.

Livrables:
- architecture cible,
- plan de travail.

## Sprint 1 - Données et validation
Objectif:
- fiabiliser ingestion CSV.

Travaux:
- loader,
- schémas attendus,
- nettoyage.

Livrable:
- datasets prêts pour analyse.

## Sprint 2 - KPI et anomalies
Objectif:
- implémenter analyse métier.

Travaux:
- analyzers domaine,
- méthode IQR.

Livrable:
- moteur analytique fonctionnel.

## Sprint 3 - Orchestration des agents
Objectif:
- connecter les étapes dans un graphe unique.

Travaux:
- état partagé,
- séquençage fixe,
- exécution sync/async.

Livrable:
- pipeline multi-agents opérationnel.

## Sprint 4 - IA générative et RAG
Objectif:
- contextualiser les analyses.

Travaux:
- intégration DeepSeek-V3.2 via Azure AI Foundry,
- indexation documents (chunking hybride Markdown + Recursive),
- retrieval sémantique (sentence-t5-base + ChromaDB).

Livrable:
- interprétation enrichie.

## Sprint 5 - Recommandations et rapport
Objectif:
- produire des actions décisionnelles.

Travaux:
- recommandation priorisée,
- rapport structuré.

Livrable:
- sortie finalisée orientée métier.

## Sprint 6 - API et UI
Objectif:
- rendre la solution utilisable de bout en bout.

Travaux:
- endpoints backend,
- pages frontend,
- intégration streaming.

Livrable:
- application full-stack.

## Sprint 7 - Stabilisation, tests et documentation
Objectif:
- améliorer robustesse, valider la couverture de tests, finaliser livrables académiques.

Travaux:
- suite de tests complète (85 tests répartis sur 4 fichiers),
- gestion d'erreurs et fallbacks,
- documentation technique,
- script `run_tests.ps1` pour persistance des rapports de tests.

Livrable:
- 85/85 tests passés,
- version démontrable en soutenance.

---

# 8. Technologies utilisées et justification

## 8.1 Backend et API
- Python: productivité et écosystème IA.
- FastAPI: performance, simplicité, validation native.
- Uvicorn: serveur ASGI léger.
- Pydantic: contrats de données robustes.

## 8.2 IA et orchestration
- LangGraph: gestion explicite du workflow multi-agents.
- LangChain: outillage LLM et composants RAG.
- DeepSeek-V3.2 via Azure AI Foundry: modèle LLM cloud, température 0.3, max 2048 tokens.

## 8.3 Data science
- Pandas/NumPy: manipulation et agrégation de données.
- Scikit-learn: régression linéaire pour tendances.

## 8.4 RAG
- sentence-transformers: embeddings sémantiques.
- ChromaDB: stockage vectoriel local et recherche de similarité.

## 8.5 Frontend
- React: architecture composable.
- Vite: cycle de dev rapide.
- Tailwind: style rapide et cohérent.
- Recharts: visualisation KPI.
- Framer Motion: fluidité UX.
- Axios/Fetch: communication API et streaming.

## 8.6 Qualité et outillage
- pytest / pytest-asyncio: suite de 85 tests unitaires et d'intégration.
- Couverture: analyzers, agents, RAG retriever, routes FastAPI.
- `run_tests.ps1`: script de lancement avec rapport persisté en UTF-8.
- ESLint: qualité frontend.
- Pyright config: cohérence environnement Python.

---

# 9. Validation, résultats et discussion

## 9.1 Résultats obtenus
- Pipeline complet exécutable.
- Calcul multi-domaines des KPI.
- Détection d'anomalies opérationnelle.
- Interprétation LLM contextualisée (DeepSeek-V3.2).
- Recommandations priorisées produites automatiquement.
- Rapport final structuré et consultable.
- Interface de chat temps réel disponible.
- **85/85 tests passés** (38 analyse, 16 agents, 15 RAG, 16 routes).

## 9.2 Valeur métier
- Réduction du temps d'analyse manuelle.
- Meilleure lisibilité des performances.
- Passage plus rapide du diagnostic à l'action.
- Support à la décision avec justification documentaire.

## 9.3 Points forts techniques
- Architecture modulaire et lisible.
- Séparation claire des responsabilités par agent.
- Bon compromis entre IA générative et règles analytiques.
- Gestion d'erreurs et fallback pour résilience.

## 9.4 Discussion critique
- Qualité finale dépendante de la qualité des données d'entrée.
- Réponses LLM variables selon formulation des prompts.
- Evaluation automatique des recommandations encore limitée.

---

# 10. Limites et perspectives

## 10.1 Limites actuelles
- Pas de gestion avancée d'authentification/autorisation.
- Persistance rapport limitée (dernier rapport principalement).
- Pas de pipeline MLOps complet (registry, monitoring dérive, CI/CD ML).
- Couverture de tests fonctionnelle (85 tests unitaires et d'intégration); les tests end-to-end avec LLM réel restent à compléter.

## 10.2 Perspectives d'amélioration
- Historisation des analyses et comparaison temporelle.
- Explicabilité renforcée des recommandations (trace KPI-source-action).
- Alertes intelligentes en temps réel.
- Multi-tenant entreprise.
- Déploiement cloud et observabilité avancée.
- Evaluation continue de qualité des sorties IA.

---

# 11. Conclusion générale

Ce projet démontre la faisabilité et l'intérêt d'une approche multi-agents pour l'aide à la décision d'entreprise. La combinaison d'analytics classiques, de modèles de langage et de RAG permet d'obtenir une chaîne complète de valeur: de la donnée brute à la recommandation actionnable.

L'approche AGILE SCRUM a facilité la livraison incrémentale et l'ajustement progressif de la solution. Le système réalisé constitue une base solide pour une industrialisation future et une adoption en contexte professionnel.

---

# Annexes recommandées

## Annexe A - User stories détaillées
Inclure les US avec priorité (Must/Should/Could) et critères d'acceptation.

## Annexe B - Backlog et planning réel
Tableau des sprints, objectifs, items traités, livrables.

## Annexe C - Endpoints API
Documenter chaque route avec exemple requête/réponse.

## Annexe D - Schémas de données
Rappeler les colonnes attendues par dataset et les règles de validation.

## Annexe E - Captures d'écran
Dashboard, upload, chat streaming, rapport final.

## Annexe F - Extraits de code clés
- Construction graphe multi-agents
- Détection anomalies IQR
- Mécanisme RAG
- Streaming SSE

---

# Tableau synthétique des sprints

| Sprint | Objectif principal | Incrément livré | Indicateur de validation |
|---|---|---|---|
| Sprint 0 | Cadrage et initialisation | Backlog + architecture | Vision validée |
| Sprint 1 | Préparation des données | Loader + validation CSV | Données prêtes |
| Sprint 2 | Analyse métier | KPI + anomalies | Sorties chiffrées cohérentes |
| Sprint 3 | Orchestration | Pipeline 5 agents | Exécution bout en bout |
| Sprint 4 | Intelligence contextuelle | LLM + RAG | Réponses enrichies |
| Sprint 5 | Décision et restitution | Recommandations + rapport | Rapport exploitable |
| Sprint 6 | Expérience utilisateur | Interface web complète | Démo fonctionnelle |
| Sprint 7 | Stabilisation | Tests + documentation | Version soutenance |

---

# Formulation prête pour la section méthodologie

La réalisation du projet a été conduite selon AGILE SCRUM, avec une planification par sprints, des livraisons incrémentales et des revues régulières. Chaque itération a produit un résultat fonctionnel mesurable, permettant d'aligner en continu les décisions techniques avec les besoins métier. Cette approche a été combinée à une logique de traitement de données inspirée de CRISP-DM pour garantir la qualité analytique du pipeline.
