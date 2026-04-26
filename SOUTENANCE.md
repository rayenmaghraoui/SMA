# SOUTENANCE — AI Business Consultant

## 1. Présentation générale du projet

### Nom du projet
AI Business Consultant

### Objectif principal
Développer un système intelligent d'aide à la décision pour PME tunisiennes, capable de:
- analyser automatiquement des données opérationnelles (finance, marketing, support client),
- détecter des anomalies de gestion,
- générer des recommandations stratégiques contextualisées au marché tunisien.

### Problème résolu
Les PME disposent souvent de données dispersées (CSV, rapports, indicateurs isolés) mais manquent:
- d'une lecture globale et cohérente des performances,
- d'une priorisation claire des actions,
- d'un lien entre données chiffrées et recommandations métier.

Le projet automatise ce cycle complet: donnée brute -> KPI -> interprétation -> recommandations -> rapport exploitable.

### Public cible / contexte d'utilisation
- Dirigeants et managers de PME tunisiennes.
- Utilisation en contexte d'analyse périodique (pilotage mensuel/trimestriel) ou diagnostic ponctuel.
- Prise en compte du contexte local (TND, fiscalité tunisienne, pratiques PME locales, documentation métier tunisienne).

### Type d'application
Application web full-stack avec backend IA:
- Frontend web (React) pour l'interaction utilisateur.
- API backend (FastAPI) pour l'orchestration métier.
- Pipeline multi-agents (LangGraph) pour le raisonnement séquentiel.
- Moteur IA local (Mistral via Ollama) + RAG (ChromaDB).


## 2. Architecture & structure du projet

### Organisation des dossiers et fichiers principaux

- Racine du projet:
  - `backend/`: logique métier, API, agents IA, analyse de données, RAG.
  - `frontend/`: interface utilisateur React.
  - `data/`: datasets CSV, uploads, dernier rapport JSON.
  - `documents/`: guides métier tunisiens servant de base de connaissance RAG.
  - `requirements.txt`: dépendances Python.
  - `pyrightconfig.json`: configuration environnement/type-check Python.

- Backend (`backend/`):
  - `main.py`: point d'entrée FastAPI, CORS, routes, health checks.
  - `config.py`: chargement des variables `.env`, chemins, paramètres LLM/RAG/API.
  - `agents/`:
    - `state.py`: état partagé `AgentState` entre agents.
    - `graph.py`: définition du graphe LangGraph (pipeline 5 agents).
    - `analysis_agent.py`, `interpretation_agent.py`, `rag_agent.py`, `recommendation_agent.py`, `report_agent.py`.
  - `analysis/`: chargement/validation des CSV + calcul KPIs + détection anomalies.
  - `rag/`: embeddings, ingestion documents, retriever ChromaDB.
  - `routes/`: endpoints REST/SSE (`/analyze`, `/upload`, `/chat`, `/report`).
  - `models/`: schémas Pydantic requêtes/réponses.

- Frontend (`frontend/src/`):
  - `pages/`: `Dashboard`, `Upload`, `Chat`, `Report`.
  - `components/`: composants UI (cartes KPI, graphiques, messages chat, progression agents, upload).
  - `hooks/`: logique état/réseau (`useAnalysis`, `useChat`).
  - `services/`: couche API (`api.js`, `chatService.js`, `uploadService.js`).

### Séparation des responsabilités

- Frontend:
  - Affichage des KPIs, du rapport et des recommandations.
  - Upload de fichiers CSV.
  - Interaction conversationnelle avec streaming SSE.
  - Navigation multi-pages (React Router).

- Backend API:
  - Exposition des routes HTTP.
  - Validation des entrées/sorties via Pydantic.
  - Gestion du cycle de vie applicatif (vérification Ollama au démarrage).
  - Persistance simple du dernier rapport (`data/last_report.json`).

- Pipeline multi-agents (cœur intelligence):
  - `analysis_agent`: calcule les KPIs + anomalies.
  - `interpretation_agent`: interprète les résultats via LLM.
  - `rag_agent`: enrichit avec le contexte documentaire tunisien.
  - `recommendation_agent`: produit des actions priorisées.
  - `report_agent`: structure un rapport final consommable par le frontend.

- Couche données / connaissances:
  - Datasets CSV opérationnels (finance, marketing, support).
  - Base vectorielle ChromaDB pour recherche sémantique dans les guides.

### Schéma du flux de données

#### Flux principal d'analyse (`POST /analyze`)
1. Frontend déclenche l'analyse.
2. Backend lance le graphe LangGraph.
3. `analysis_agent` charge/valide/nettoie les CSV puis calcule KPIs + anomalies (IQR).
4. `interpretation_agent` construit une analyse textuelle via Mistral (Ollama).
5. `rag_agent` interroge ChromaDB pour extraire des passages pertinents des guides.
6. `recommendation_agent` génère 5 recommandations priorisées.
7. `report_agent` assemble le rapport final JSON.
8. Backend sauvegarde le rapport (`data/last_report.json`) et retourne la réponse API.
9. Frontend affiche dashboard/rapport.

#### Flux conversationnel (`POST /chat`, SSE)
1. Frontend envoie une question utilisateur.
2. Backend exécute le pipeline en mode streaming.
3. Des événements SSE sont renvoyés progressivement:
   - `step` (étape en cours),
   - `token` (texte interprétation),
   - `report` (rapport structuré),
   - `done` (fin).
4. Frontend met à jour l'UI en temps réel (progression + message assistant).


## 3. Stack technique & outils utilisés

### Langages de programmation
- Python (backend, IA, analyse des données, RAG).
- JavaScript / JSX (frontend React).
- SQL embarqué via SQLite (stockage interne ChromaDB).

### Frameworks et librairies (rôle précis)

#### Backend / IA
- FastAPI: création des endpoints REST/SSE, validation automatique, documentation OpenAPI.
- Uvicorn: serveur ASGI d'exécution de l'API.
- LangGraph: orchestration séquentielle du pipeline multi-agents.
- LangChain (+ `langchain-community`, `langchain-huggingface`, `langchain-ollama`): intégration LLM, embeddings et composants RAG.
- Ollama + modèle Mistral: exécution locale du LLM pour interprétation et recommandations.
- Pandas / NumPy: préparation des données et calculs KPI.
- Scikit-learn: régressions linéaires pour déterminer les tendances temporelles.
- ChromaDB: base vectorielle locale pour l'indexation et la recherche sémantique.
- Sentence Transformers (`sentence-transformers/sentence-t5-base`): génération d'embeddings.
- Pydantic v2: schémas de validation des requêtes/réponses API.
- python-dotenv: chargement centralisé des variables d'environnement.
- HTTPX: vérification de disponibilité d'Ollama (health/lifespan).

#### Frontend
- React 18: architecture UI en composants fonctionnels.
- React Router v6: routage multi-pages (`/`, `/upload`, `/chat`, `/report`).
- Axios: client HTTP pour les routes API standard.
- Fetch + ReadableStream: gestion du streaming SSE sur la route chat.
- Framer Motion: animations UI et transitions de pages.
- Recharts: visualisation de données KPI (ex: ROI par canal).

### Outils de développement

#### Frontend
- Vite: bundler/dev server rapide.
- `@vitejs/plugin-react`: support React dans Vite.
- Tailwind CSS + PostCSS + Autoprefixer: système de style utilitaire et pipeline CSS.
- ESLint (script npm `lint`): contrôle qualité JS/JSX.
- npm: gestionnaire de paquets frontend.

#### Backend
- pip + `requirements.txt`: gestionnaire de dépendances Python.
- Pyright (`pyrightconfig.json`): configuration de l'environnement Python (`.venv`) et du typage statique.
- pytest + pytest-asyncio: tests backend/asynchrones (dépendances présentes).

### Base de données et ORM
- Base principale: pas de SGBD relationnel métier (pas d'ORM type SQLAlchemy).
- Stockages utilisés:
  - ChromaDB (vector store local) pour le RAG.
  - Fichier JSON (`data/last_report.json`) pour conserver le dernier rapport généré.

### Outils DevOps / déploiement (présents dans le projet)
- Uvicorn pour exécution locale du backend.
- Vite pour exécution locale du frontend.
- Ollama pour héberger localement le modèle LLM.

Aucun pipeline CI/CD, conteneur Docker, orchestrateur ou configuration cloud n'est explicitement présent dans ce workspace.
