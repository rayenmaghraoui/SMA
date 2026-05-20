# AI Business Consultant — Système Multi-Agents

Projet de Fin d'Études (PFE) — Système d'aide à la décision pour **PME tunisiennes**.

Analyse des données opérationnelles (ventes, régions, catégories, canaux, KPIs), détection d'anomalies, enrichissement **RAG** (guides métier) et recommandations stratégiques en **français**, via un pipeline **LangGraph** et une interface **React**.

---

## Fonctionnalités

| Fonction | Description |
|----------|-------------|
| **Dashboard** | KPIs, graphiques, résumé exécutif |
| **Upload** | Import de fichiers CSV (validation + stockage) |
| **Chat** | Questions en langage naturel (streaming SSE) |
| **Rapport** | Rapport structuré (recommandations, anomalies, sources RAG) |
| **SQL Agent** | Exploration des données : question → SQL (DuckDB) → tableau / graphique |

---

## Architecture

```
┌─────────────┐     REST/SSE     ┌─────────────┐     LangGraph     ┌─────────────────────────────┐
│   Frontend  │ ───────────────▶ │   FastAPI   │ ────────────────▶ │ 5 agents (pipeline strat.)  │
│  React+Vite │                  │   Backend   │                   │ analysis → interpretation   │
└─────────────┘                  └─────────────┘                   │ → rag → recommendation    │
                                                                   │ → report                  │
                                                                   └─────────────────────────────┘
                                              │
                    ┌─────────────────────────┼─────────────────────────┐
                    ▼                         ▼                         ▼
             ┌─────────────┐          ┌─────────────┐          ┌─────────────┐
             │   Pandas    │          │  ChromaDB   │          │  DeepSeek   │
             │  Scikit     │          │  + T5 emb.  │          │  Azure AI   │
             └─────────────┘          └─────────────┘          └─────────────┘
                                              │
                    Question données ─────────┴──▶ intent_router → SQL (DuckDB) → résultat
```

**Pipeline stratégique (chat / analyse complète) :**
```
analysis_agent → interpretation_agent → rag_agent → recommendation_agent → report_agent → END
```

**SQL Agent (questions de données) :**
```
question → intent_router → generate_sql → validate_sql → execute_sql (DuckDB) → SqlResult
```

---

## Types de données supportés

### Données opérationnelles (analyse + SQL)

Le pipeline attend **5 fichiers CSV** dans `data/uploads/` avec **noms et colonnes fixes** :

| Fichier | Rôle | Colonnes principales |
|---------|------|----------------------|
| `01_donnees_vente.csv` | Transactions | `invoice_id`, `product_name`, `category`, `quantity`, `unit_price_tnd`, `revenue_tnd`, `customer_id`, `customer_region`, `sale_date`, `sales_channel`, `payment_method`, `estimated_profit` |
| `02_analyse_region.csv` | Par région | `customer_region`, `ca_total`, `profit_total`, `nb_transactions`, `panier_moyen` |
| `03_analyse_categorie.csv` | Par catégorie | `category`, `ca_total`, `profit_total`, `nb_transactions`, `quantite_vendue`, `prix_moyen` |
| `04_analyse_canaux.csv` | Par canal | `sales_channel`, `ca_total`, `nb_transactions`, `panier_moyen` |
| `05_kpis_globaux.csv` | KPIs globaux | `indicateur`, `valeur` |

Types de valeurs : texte, entiers, décimaux, dates (`YYYY-MM-DD`), montants en **TND**.

### Upload via l'interface (`POST /upload`)

- Format accepté : **`.csv`** uniquement (max ~10 Mo).
- Détection automatique (schémas legacy) : **finance**, **marketing**, **support** selon les colonnes.
- Fichiers stockés dans `data/uploads/`.
- **Important :** l'analyse complète (`POST /analyze`) charge les **5 fichiers nommés ci-dessus**. Les CSV uploadés avec d'autres noms doivent correspondre à ce format pour être utilisés.

### RAG (base de connaissances)

- Sources : fichiers **Markdown** (`.md`) dans `documents/`.
- Exemples attendus : guides gestion PME, finance, KPIs, logistique, RH Tunisie.
- Indexation : `python -m backend.rag.ingest` → stockage dans `backend/rag/chroma_db/`.

### Entrées / sorties applicatives

| Entrée | Sortie |
|--------|--------|
| Question texte (FR) | Texte + rapport JSON (chat / analyse) |
| Question SQL (FR) | SQL, lignes, graphique Recharts |
| — | Non supporté sans modification : Excel, JSON, PDF, BDD externes, API temps réel |

---

## Stack technique

### Backend

| Composant | Technologie |
|-----------|-------------|
| API | FastAPI, Uvicorn |
| Agents | LangGraph, LangChain |
| Analyse | Pandas, NumPy, Scikit-learn |
| Vector DB | ChromaDB |
| Embeddings | `sentence-transformers/sentence-t5-base` |
| LLM | **DeepSeek-V3.2** via **Azure AI Foundry** |
| SQL in-memory | DuckDB |

### Frontend

| Composant | Technologie |
|-----------|-------------|
| Framework | React 18 |
| Build | Vite |
| Styling | Tailwind CSS (thème cyan) |
| Animations | Framer Motion |
| Graphiques | Recharts |
| HTTP / SSE | Axios, fetch (streaming) |
| Routing | React Router v6 |

---

## Prérequis

- **Python 3.10+** (Docker backend : image `python:3.12-slim`)
- **Node.js 18+**
- Compte **Azure AI Foundry** avec accès **DeepSeek-V3.2**
- (Optionnel) **Docker** + **Docker Compose** pour déploiement conteneurisé

---

## Installation (développement local)

### 1. Cloner et installer

```bash
git clone <url-du-repo>
cd "SMA assistant"

# Environnement virtuel recommandé
python -m venv .venv
# Windows
.venv\Scripts\activate
# Linux / macOS
# source .venv/bin/activate

pip install -r requirements.txt

cd frontend
npm install
cd ..
```

### 2. Fichier `.env` (racine du projet)

```env
# LLM — Azure AI Foundry (DeepSeek-V3.2)
AZURE_OPENAI_API_KEY=<votre_clé>
AZURE_OPENAI_ENDPOINT=https://<ressource>.services.ai.azure.com/openai/v1/
AZURE_OPENAI_MODEL=DeepSeek-V3.2
LLM_TEMPERATURE=0.3
LLM_MAX_TOKENS=2048

# Embeddings
EMBEDDING_MODEL=sentence-transformers/sentence-t5-base

# Chemins
DATA_DIR=./data
DOCUMENTS_DIR=./documents
CHROMA_DB_PATH=./backend/rag/chroma_db
UPLOADS_DIR=./data/uploads

# RAG
RAG_CHUNK_SIZE=500
RAG_CHUNK_OVERLAP=50
RAG_TOP_K=3

# API
API_HOST=0.0.0.0
API_PORT=8000
FRONTEND_URL=http://localhost:5173
DEBUG=true
```

### 3. Données CSV

Placer les 5 fichiers dans `data/uploads/` (voir tableau ci-dessus).

### 4. Guides RAG (optionnel mais recommandé)

Ajouter des fichiers `.md` dans `documents/`, puis :

```bash
python -m backend.rag.ingest
```

Exemple de sortie :
```
✓ Ingestion réussie !
  → N chunks indexés
  → Base ChromaDB : ./backend/rag/chroma_db
```

### 5. Frontend — variable API

Créer `frontend/.env` si besoin :

```env
VITE_API_URL=http://localhost:8000
```

---

## Lancement (local)

**Terminal 1 — Backend :**
```bash
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

**Terminal 2 — Frontend :**
```bash
cd frontend
npm run dev
```

| Service | URL |
|---------|-----|
| Frontend | http://localhost:5173 |
| API Swagger | http://localhost:8000/docs |
| Health | http://localhost:8000/health |

---

## Docker

Le projet inclut une stack **backend + frontend** (LLM via variables Azure dans `.env`).

```bash
# À la racine, avec .env configuré
docker compose up --build
```

| Service | Port hôte | Image |
|---------|-----------|--------|
| Backend | 8000 | `backend/Dockerfile` |
| Frontend | 5173 → Nginx :80 | `frontend/Dockerfile` |

**Volumes persistants :**
- `chroma_data` → index ChromaDB
- `uploads_data` → fichiers CSV uploadés

**Notes :**
- Le premier démarrage backend peut être long (téléchargement modèle d'embeddings).
- Vérifier `GET /health` : statut Azure doit être joignable pour les agents LLM.
- En production Docker, le frontend appelle l'API via le proxy Nginx (`/api`).

---

## API principale

| Méthode | Route | Description |
|---------|-------|-------------|
| `POST` | `/analyze` | Lance le pipeline complet (5 agents) |
| `POST` | `/upload` | Upload d'un CSV |
| `GET` | `/uploads` | Liste des CSV uploadés |
| `POST` | `/chat` | Chat avec streaming SSE (+ routage SQL / stratégique) |
| `POST` | `/chat/simple` | Chat sans streaming (tests) |
| `POST` | `/sql/query` | Question → SQL → résultat JSON |
| `POST` | `/sql/query/export` | Export CSV des résultats SQL |
| `GET` | `/report` | Dernier rapport (404 si absent) |
| `GET` | `/report/latest` | Dernier rapport sans 404 (`has_report`) |
| `GET` | `/report/kpis` | KPIs du dernier rapport |
| `GET` | `/health` | Santé API + Azure |

### Exemple — analyse

```bash
curl -X POST http://localhost:8000/analyze \
  -H "Content-Type: application/json" \
  -d "{\"use_defaults\": true}"
```

Le rapport est persisté (`data/last_report.json` + mémoire) après une analyse ou un chat réussi.

### Exemple — chat

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d "{\"message\": \"Comment améliorer la satisfaction client ?\"}"
```

Événements SSE : `step`, `token`, `report`, `done` (ou `sql_result` pour les questions données).

### Exemple — SQL

```bash
curl -X POST http://localhost:8000/sql/query \
  -H "Content-Type: application/json" \
  -d "{\"question\": \"Top 5 régions par chiffre d affaires\"}"
```

---

## Structure du projet

```
SMA assistant/
├── .env
├── requirements.txt
├── README.md
├── CLAUDE.md
├── docker-compose.yml
├── backend/
│   ├── Dockerfile
│   ├── main.py
│   ├── config.py
│   ├── analysis/          # loader, analyzers, anomaly_detector
│   ├── agents/            # LangGraph (5 agents)
│   ├── rag/               # embeddings, ingest, retriever, chroma_db/
│   ├── sql_agent/         # DuckDB, NL→SQL, intent_router
│   ├── routes/            # analyze, upload, chat, report, sql
│   ├── models/
│   └── tests/
├── data/
│   ├── uploads/           # 5 CSV requis pour l'analyse
│   └── last_report.json   # dernier rapport sauvegardé
├── documents/             # guides Markdown (RAG)
└── frontend/
    ├── Dockerfile
    ├── package.json
    └── src/
        ├── pages/         # Dashboard, Upload, Chat, Report
        ├── components/
        ├── hooks/
        └── services/
```

---

## Pages frontend

| Page | Route | Description |
|------|-------|-------------|
| Dashboard | `/` | KPIs, graphiques, bouton « Lancer l'analyse » |
| Upload | `/upload` | Drag-and-drop CSV |
| Chat | `/chat` | Assistant IA (streaming) |
| Rapport | `/report` | Rapport complet (après analyse) |

---

## Tests

```bash
# Tous les tests
python -m pytest backend/tests/ -v

# Rapport fichier (Windows)
.\run_tests.ps1
```

| Module | Fichier | Contenu |
|--------|---------|---------|
| Analyse | `test_analysis.py` | Analyzers, anomalies |
| Agents | `test_agents.py` | Pipeline LangGraph |
| RAG | `test_rag.py` | Retriever ChromaDB |
| Routes | `test_routes.py` | API FastAPI |
| SQL | `test_sql_agent.py` | Validator, executor, routes SQL |

---

## Commandes utiles

| Action | Commande |
|--------|----------|
| Installer Python | `pip install -r requirements.txt` |
| Installer frontend | `cd frontend && npm install` |
| Indexer RAG | `python -m backend.rag.ingest` |
| Backend | `uvicorn backend.main:app --reload --port 8000` |
| Frontend | `cd frontend && npm run dev` |
| Docker | `docker compose up --build` |
| Tests | `python -m pytest backend/tests/ -v` |

---

## Dépannage

| Problème | Piste de solution |
|----------|------------------|
| Erreur LLM / agents vides | Vérifier `AZURE_OPENAI_*` dans `.env` et `GET /health` |
| Rapport vide sur `/report` | Lancer d'abord `POST /analyze` ou une question via `/chat` |
| Dashboard sans KPIs | Même chose : besoin d'un rapport généré (`/report/latest`) |
| Upload OK mais analyse inchangée | Vérifier que les 5 CSV sont bien dans `data/uploads/` avec les bons noms |
| RAG sans contexte | Lancer `python -m backend.rag.ingest` et vérifier `documents/*.md` |
| SQL : table manquante | Présence des 5 fichiers CSV ; redémarrer l'API après remplacement des fichiers |

---

## Phases du projet

- [x] Phase 1 — Configuration, loader, tests données
- [x] Phase 2 — Analyzers, analysis agent, `/analyze`
- [x] Phase 3 — RAG (sentence-t5-base) + rag agent
- [x] Phase 4 — Agents LLM, rapport, frontend React
- [x] Phase 5 — Tests unitaires et intégration
- [x] Phase 6 — SQL Agent (DuckDB + intent routing)
- [x] Phase 7 — Docker (backend + frontend)
- [x] Données — Migration vers 5 jeux CSV (ventes / régions / catégories / canaux / KPIs)

---

## Auteur

Projet PFE — **AI Business Consultant** pour PME tunisiennes.

Documentation technique détaillée : voir `CLAUDE.md`.
