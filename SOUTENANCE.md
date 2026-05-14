# SOUTENANCE — AI Business Consultant

## 1. Présentation générale du projet

### Nom du projet
AI Business Consultant

### Objectif principal
Développer un système intelligent d'aide à la décision pour PME tunisiennes, capable de:
- analyser automatiquement des données opérationnelles (cinq datasets CSV : ventes, régions, catégories, canaux, KPIs globaux),
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
- LLM cloud (DeepSeek-V3.2 via Azure AI Foundry) + RAG (ChromaDB).

### Approche méthodologique complémentaire : CRISP-DM
En complément de l'approche AGILE SCRUM utilisée pour le pilotage du projet, la démarche CRISP-DM a été retenue pour structurer la partie data science et analyse des données. Cette méthode est particulièrement adaptée à ce projet, car elle permet de relier explicitement le besoin métier, l'exploration des données, leur préparation, la modélisation, l'évaluation des résultats et enfin le déploiement de la solution.

#### Les 6 étapes clés de CRISP-DM appliquées au projet

1. **Compréhension du métier (Business Understanding)**
  Cette étape consiste à identifier le besoin réel des PME tunisiennes en matière d'aide à la décision. L'objectif est de concevoir un système capable d'analyser les données opérationnelles, de détecter les anomalies de gestion et de produire des recommandations adaptées au contexte économique et réglementaire local.

2. **Compréhension des données (Data Understanding)**
  Cette phase permet d'explorer les cinq jeux de données utilisés dans le projet afin d'en analyser la structure, le contenu, la cohérence et la qualité. Elle vise à vérifier la pertinence des variables disponibles pour les analyses futures.

3. **Préparation des données (Data Preparation)**
  Les données sont ensuite nettoyées, normalisées, validées et organisées de manière à être exploitables par les différents modules du système. Cette étape inclut notamment le traitement des valeurs manquantes, la standardisation des formats et la structuration des fichiers pour l'analyse.

4. **Modélisation (Modeling)**
  Cette étape correspond à la mise en œuvre des traitements analytiques et intelligents. Le projet applique ici le calcul des KPI, la détection des anomalies, l'exécution des requêtes SQL en langage naturel et l'orchestration du pipeline multi-agents.

5. **Évaluation (Evaluation)**
  Les résultats obtenus sont ensuite évalués afin de vérifier leur cohérence, leur fiabilité et leur valeur métier. Cette étape permet de valider la qualité des KPI calculés, la pertinence des anomalies détectées et la qualité des recommandations générées.

6. **Déploiement (Deployment)**
  Enfin, la solution est intégrée dans une application web complète accessible à l'utilisateur final. Le déploiement permet de mettre à disposition un outil opérationnel combinant analyse, interaction conversationnelle, visualisation des résultats et génération de rapports.


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
  - `routes/`: endpoints REST/SSE (`/analyze`, `/upload`, `/chat`, `/report`, `/sql/query`).
  - `models/`: schémas Pydantic requêtes/réponses.
  - `sql_agent/`: agent SQL autonome (`db.py`, `validator.py`, `generator.py`, `executor.py`, `intent_router.py`).

- Frontend (`frontend/src/`):
  - `pages/`: `Dashboard`, `Upload`, `Chat`, `Report`.
  - `components/`: composants UI (cartes KPI, graphiques, messages chat, progression agents, upload, **SqlResult** pour affichage résultats SQL).
  - `hooks/`: logique état/réseau (`useAnalysis`, `useChat`).
  - `services/`: couche API (`api.js`, `chatService.js`, `uploadService.js`).

### Séparation des responsabilités

- Frontend:
  - Affichage des KPIs, du rapport et des recommandations.
  - Upload de fichiers CSV.
  - Interaction conversationnelle avec streaming SSE.
  - Affichage des résultats SQL (tableau + graphique Recharts + export CSV).
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

- SQL Agent (exploration de données):
  - `intent_router`: analyse chaque question et décide entre "sql" ou "strategic".
  - `generator`: envoie la question à DeepSeek qui génère une requête SQL + viz_type.
  - `validator`: sécurise la requête (SELECT only, mots-clés interdits, injection SQL).
  - `executor`: exécute la requête sur DuckDB (in-memory, 3 CSV chargés comme tables), timeout 10s, max 500 lignes.

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
2. Backend classe l'intention : **"sql"** (exploration de données) ou **"strategic"** (analyse stratégique).
3. Si **"sql"** :
   - DeepSeek génère une requête SQL + viz_type.
   - La requête est validée (sécurité) puis exécutée sur DuckDB.
   - Le résultat (tableau + données graphique) est envoyé en SSE via événement `sql_result`.
4. Si **"strategic"** :
   - Backend exécute le pipeline LangGraph (5 agents) en mode streaming.
   - Des événements SSE sont renvoyés progressivement :
     - `step` (étape en cours),
     - `token` (texte interprétation),
     - `report` (rapport structuré),
     - `done` (fin).
5. Frontend met à jour l'UI en temps réel.


## 3. Stack technique & outils utilisés

- Langages de programmation
- Python (backend, IA, analyse des données, RAG, SQL agent).
- JavaScript / JSX (frontend React).
- SQL (généré par le LLM, exécuté via DuckDB in-memory).
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
- DuckDB: base de données analytique in-memory. Charge les 5 CSV comme tables SQL (ex. `ventes`, `regions`, `categories`, `canaux`, `kpis`) pour l'exploration par langage naturel.
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
  - DuckDB in-memory pour l'exécution des requêtes SQL générées par le LLM.
  - Fichier JSON (`data/last_report.json`) pour conserver le dernier rapport généré.

### Outils DevOps / déploiement (présents dans le projet)
- Uvicorn pour exécution locale du backend.
- Vite pour exécution locale du frontend.
- Docker + docker-compose pour la containerisation (Dockerfiles présents pour frontend et backend).
- Azure AI Foundry pour l'hébergement cloud du modèle LLM (DeepSeek-V3.2).

## 4. Points forts techniques (Arguments Jury)

### 4.1. Base vectorielle et système RAG (Retrieval-Augmented Generation)
Afin de garantir que les recommandations de l'IA sont pertinentes pour une PME tunisienne, le projet intègre une base vectorielle locale :
- **Technologie :** Base vectorielle **ChromaDB**.
- **Modèle d'Embedding :** Utilisation de `sentence-transformers/sentence-t5-base` (transforme les textes en vecteurs mathématiques de 768 dimensions).
- **Fonctionnement :** 5 guides métiers tunisiens (lois du travail, fiscalité, logistique, etc.) ont été découpés en sous-parties (chunks) et indexés. L'Agent RAG effectue une recherche de "similarité cosinus" pour extraire l'information pertinente.
- **Pourquoi c'est un point fort :** Cela montre que le système ne se contente pas des connaissances générales du modèle, mais s'appuie sur une vraie base de connaissances métier locale (lois et contextes réels).

### 4.2. Mécanismes Anti-Hallucination
Dans un système d'aide à la décision (notamment financier), la fiabilité est primordiale. Quatre barrières anti-hallucination ont été implémentées :
1. **L'ancrage documentaire (RAG) :** Le LLM est "forcé" de baser ses réponses sur les documents extraits de ChromaDB, évitant ainsi l'invention de lois ou de normes.
2. **Paramétrage restrictif (Température = 0.3) :** Le modèle d'IA a été configuré avec une température basse de `0.3`, favorisant la précision, la cohérence et la logique factuelle plutôt que la créativité.
3. **Séparation Calcul / Interprétation :** Les LLMs étant sujets aux erreurs mathématiques, ils ne calculent rien. Ce sont des librairies Python déterministes (Pandas, DuckDB) qui font les vrais calculs analytiques. L'IA ne reçoit que les résultats exacts pour les commenter, évitant les hallucinations numériques.
4. **Validation stricte (Pydantic & Validateur SQL) :** Les données circulant entre les agents sont sécurisées par des schémas Pydantic. De plus, l'Agent SQL intègre un filtre de sécurité qui rejette toute requête contenant des tables inventées ou des commandes interdites (uniquement du `SELECT`).

## 5. Remarques à mettre en avant devant le jury

### 5.1. Pourquoi ce projet est pertinent pour les PME tunisiennes
- Le projet répond à un besoin concret : transformer des fichiers CSV isolés en un outil d'aide à la décision structuré.
- Il est conçu pour un contexte local : Dinar Tunisien, TVA à 19%, droit du travail tunisien et pratiques PME tunisiennes.
- Il combine l'analyse quantitative (KPI, anomalies, SQL) et l'analyse qualitative (interprétation, recommandations, contexte documentaire local).

### 5.2. Rôle des agents et leur valeur ajoutée
- **analysis_agent** : c'est le socle analytique. Il calcule les KPIs financiers, marketing et support, et détecte les anomalies via IQR. Il garantit des résultats explicables et mesurables.
- **interpretation_agent** : il transforme les KPIs en insights compréhensibles pour un dirigeant. Il joue le rôle de traducteur entre données chiffrées et langage métier.
- **rag_agent** : il apporte le contexte métier tunisien. Il utilise la base vectorielle pour récupérer des passages précis des guides et ainsi « ancrer » les recommandations.
- **recommendation_agent** : il priorise les actions. Il ne donne pas seulement un constat, il propose des actions concrètes et hiérarchisées.
- **report_agent** : il met en forme un rapport final structuré, prêt à être présenté et consommé par l'utilisateur.

### 5.3. Choix technologiques et justifications
- **FastAPI** : choix pertinent pour une API moderne, asynchrone et facilement testable avec Pydantic. Il facilite la construction de routes REST et SSE.
- **React + Vite + Tailwind** : choix adapté pour une interface rapide, réactive et maintenable. Vite permet un développement très rapide tandis que Tailwind assure une UI cohérente.
- **LangGraph** : il permet d'organiser un pipeline de raisonnement en plusieurs étapes, ce qui rend l'intelligence modulaire et plus simple à déboguer.
- **ChromaDB + sentence-t5-base** : combinaison adaptée pour un RAG local. ChromaDB est légère et performante, tandis que sentence-t5-base produit des embeddings de qualité pour la similarité sémantique.
- **DuckDB** : excellent choix pour des requêtes analytiques in-memory sur des CSV. Il autorise un SQL rapide sans nécessiter une base de production lourde.
- **Azure AI Foundry / DeepSeek-V3.2** : permet d'utiliser un modèle LLM puissant et disponible en cloud, tout en conservant un contrôle sur la température et les entrées.
- **Pydantic** : renforce la solidité du backend en validant stricte ment les requêtes et les réponses.

### 5.4. Architecture et séparation claire des responsabilités
- Le frontend reste une couche de présentation et de navigation.
- Le backend orchestre la logique métier, le calcul et la génération de réponses.
- La base vectorielle et les documents métier sont séparés du calcul des KPI, ce qui facilite les évolutions futures.
- L'agent SQL est séparé de l'agent stratégique, ce qui permet de distinguer clairement l'analyse de données et la conversation métier.

### 5.5. Qualité et maîtrise technique
- L'utilisation de **tests** (`pytest`) permet de valider le comportement du backend et des agents.
- Le projet respecte des conventions de code : typage Python, docstrings en français, gestion des erreurs, logging.
- Le dossier `backend/config.py` centralise les chemins, paramètres et variables d'environnement.
- Le système évite les mauvaises pratiques courantes : pas de calculs faits par le LLM, pas de `print()` en production.

### 5.6. Bonnes pratiques de déploiement
- **Docker** permet de contenir le backend et le frontend séparément.
- **docker-compose** permet de lancer l'ensemble de la solution plus facilement.
- La présentation peut mentionner que la solution est conçue pour être conteneurisée et déployable sur un cloud ou un cluster local.

### 5.7. Limites identifiées et perspectives d'amélioration
- pour l'instant, le projet est adapté aux PME et aux datasets structurés au format CSV ; une étape suivante serait d'ajouter la prise en charge de fichiers Excel ou d'APIs externes.
- le modèle RAG fonctionne avec des documents statiques ; une évolution possible est d'ajouter une ingestion automatique de nouvelles sources réglementaires.
- le backend pourrait être enrichi avec un système de logs utilisateur pour analyser l'utilisation et améliorer les recommandations.
- la robustesse pourrait être renforcée en ajoutant des tests d'intégration pour le pipeline LangGraph complet.

### 5.8. Argument clé à répéter au jury
- Le projet n'est pas seulement un chatbot IA : c'est un outil hybride qui associe des calculs analytiques exacts, une base documentaire locale (RAG) et un moteur de recommandations métier.
- Cette architecture réduit les risques d'hallucination et augmente la confiance du décideur en fournissant des résultats chiffrés et contextualisés.
- Le travail montre à la fois une maîtrise technique (backend, frontend, IA et DevOps) et une compréhension métier (contexte tunisien, fiscalité, droit du travail, besoins PME).
