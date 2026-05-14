# AI Business Consultant — Système Multi-Agents

Projet de Fin d'Études (PFE) — Système d'aide à la décision pour PME tunisiennes.

## Description

Ce système analyse les données opérationnelles d'entreprises tunisiennes (5 jeux CSV : ventes, régions, catégories, canaux, KPIs globaux), détecte les problèmes de gestion et produit des recommandations stratégiques adaptées au contexte local.

## Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Frontend  │────▶│   FastAPI   │────▶│  LangGraph  │
│    React    │ REST│   Backend   │     │   Agents    │
└─────────────┘ SSE └─────────────┘     └─────────────┘
                                               │
                    ┌──────────────────────────┼──────────────────────────┐
                    ▼                          ▼                          ▼
             ┌─────────────┐           ┌─────────────┐           ┌─────────────┐
             │  Analysis   │           │     RAG     │           │     LLM     │
             │   Pandas    │           │  ChromaDB   │           │  DeepSeek   │
             └─────────────┘           └─────────────┘           └─────────────┘
```

**Pipeline complet des 5 agents (questions stratégiques) :**
```
analysis_agent → interpretation_agent → rag_agent → recommendation_agent → report_agent → END
```

**SQL Agent (questions de données) :**
```
question → intent_router → generate_sql (DeepSeek) → validate_sql → execute_sql (DuckDB) → SqlResult
```

## Stack Technique

### Backend
| Composant | Technologie |
|-----------|-------------|
| API | FastAPI |
| Agents | LangGraph |
| Analyse données | Pandas, NumPy, Scikit-learn |
| Base vectorielle | ChromaDB |
| Embeddings | sentence-transformers/sentence-t5-base |
| LLM | DeepSeek-V3.2 via Azure AI Foundry |
| SQL In-Memory | DuckDB |

### Frontend
| Composant | Technologie |
|-----------|-------------|
| Framework | React 18 |
| Build | Vite |
| Styling | Tailwind CSS |
| Animations | Framer Motion |
| Graphiques | Recharts |
| HTTP | Axios |
| Streaming | SSE (Server-Sent Events) |
| Routing | React Router v6 |

---

## Installation

### Prérequis

- Python 3.10+
- Node.js 18+
- Compte Azure AI Foundry avec accès DeepSeek-V3.2

### Étape 1 : Cloner et installer les dépendances

```bash
cd "c:/Users/rayen/Desktop/SMA assistant"

# Backend
pip install -r requirements.txt

# Frontend
cd frontend
npm install
cd ..
```

### Étape 2 : Configurer le fichier .env

Créer un fichier `.env` à la racine du projet :
```env
AZURE_OPENAI_API_KEY=<votre_clé>
AZURE_OPENAI_ENDPOINT=https://<ressource>.services.ai.azure.com/openai/v1/
AZURE_OPENAI_MODEL=DeepSeek-V3.2
LLM_TEMPERATURE=0.3
LLM_MAX_TOKENS=2048
EMBEDDING_MODEL=sentence-transformers/sentence-t5-base
DATA_DIR=./data
DOCUMENTS_DIR=./documents
CHROMA_DB_PATH=./backend/rag/chroma_db
UPLOADS_DIR=./data/uploads
RAG_CHUNK_SIZE=500
RAG_CHUNK_OVERLAP=50
RAG_TOP_K=3
API_HOST=0.0.0.0
API_PORT=8000
FRONTEND_URL=http://localhost:5173
DEBUG=true
```

### Étape 4 : Préparer les données

**4.1 — Fichiers CSV (dans `data/uploads/`)**

Le projet utilise désormais 5 jeux de données d'entrée placés dans `data/uploads/` :
```
data/uploads/
├── 01_donnees_vente.csv        # ventes par produit / transaction
├── 02_analyse_region.csv       # ventes/région, métriques régionales
├── 03_analyse_categorie.csv    # analyse par catégorie / produit
├── 04_analyse_canaux.csv       # performance par canal (online/offline)
└── 05_kpis_globaux.csv         # KPIs agrégés et métriques globales
```
Ces fichiers remplacent l'ancien format 3-CSV ; l'agent SQL et les loaders ont été adaptés pour charger ces 5 tables.

**4.2 — Guides Markdown (dans `documents/`)**

Tu dois créer ces 5 fichiers :
```
documents/
├── guide_gestion_entreprises_tunisiennes.md
├── guide_gestion_financiere_tunisie.md
├── guide_interpretation_kpis_tunisie.md
├── guide_logistique_supply_chain_tunisie.md
└── guide_rh_droit_travail_tunisie.md
```

### Étape 5 : Indexer les documents RAG

```bash
python -m backend.rag.ingest
```

Tu verras un résumé :
```
✓ Ingestion réussie !
  → 45 chunks indexés
  → Base ChromaDB : ./backend/rag/chroma_db
```

---

## Lancement

### Terminal 1 : Backend
```bash
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

### Terminal 3 : Frontend
```bash
cd frontend
npm run dev
```

### Accès

| Service | URL |
|---------|-----|
| Frontend | http://localhost:5173 |
| API Swagger | http://localhost:8000/docs |
| Health Check | http://localhost:8000/health |

---

## Utilisation de l'API

### POST /analyze

Lance l'analyse complète des données (pipeline 5 agents).

```bash
curl -X POST http://localhost:8000/analyze
```

**Réponse :**
```json
{
  "success": true,
  "kpis": {
    "finance": { "revenue_total": 2191187, "profit_total": 547796, "profit_margin": 25.0, "trend": "stable" },
    "marketing": { "best_channel": "Réseaux sociaux", "top_revenue_channel": "Magasin physique" },
    "categories": { "top_category_by_revenue": "Mobilier", "top_category_by_conv": "Textile" },
    "ventes": { "best_product": "Table en Bois", "best_region": "Tunis", "best_channel": "Magasin physique" },
    "regions": { "top_region": "Tunis", "avg_ticket_global": 1095 }
  },
  "anomalies": [...],
  "recommendations": [...],
  "report": {...}
}
```

### POST /upload

Upload un fichier CSV pour analyse personnalisée.

```bash
curl -X POST -F "file=@mon_fichier.csv" http://localhost:8000/upload
```

### POST /chat

Interface conversationnelle avec streaming SSE et routage d'intention automatique.

```bash
curl -X POST -H "Content-Type: application/json" \
  -d '{"message": "Analysez les performances financières"}' \
  http://localhost:8000/chat
```

**Format SSE — question stratégique :**
```
data: {"type": "step", "content": "Analyse des données en cours..."}
data: {"type": "token", "content": "Voici mon analyse..."}
data: {"type": "report", "content": "{...}"}
data: {"type": "done", "content": ""}
```

**Format SSE — question SQL :**
```
data: {"type": "sql_result", "content": "{sql, rows_preview, total_rows, chart_data, message}"}
data: {"type": "done", "content": ""}
```

### POST /sql/query

Interroge directement les données en langage naturel (via DuckDB).

```bash
curl -X POST -H "Content-Type: application/json" \
  -d '{"question": "Montre-moi le top 5 des régions par chiffre d affaires"}' \
  http://localhost:8000/sql/query
```

**Réponse :**
```json
{
  "success": true,
  "sql": "SELECT customer_region, CA_Total FROM regions ORDER BY CA_Total DESC LIMIT 5",
  "rows_preview": [{"customer_region": "Tunis", "CA_Total": 598464}],
  "total_rows": 5,
  "chart_data": {"x_key": "campaign_id", "y_keys": ["conversions"], "data": [...]},
  "message": "5 ligne(s) retournée(s).",
  "errors": []
}
```

### POST /sql/query/export

Même que `/sql/query` mais retourne les données au format CSV téléchargeable.

### GET /report

Récupère le dernier rapport généré.

```bash
curl http://localhost:8000/report
```

### GET /health

Vérifie l'état de l'API et d'Azure AI Foundry.

```bash
curl http://localhost:8000/health
```

---

## Structure du Projet

```
ai-business-consultant/
├── .env                          # Variables d'environnement
├── requirements.txt              # Dépendances Python
├── README.md                     # Ce fichier
├── CLAUDE.md                     # Instructions pour Claude
│
├── data/                         # Données CSV
│   ├── uploads/                  # Fichiers uploadés (5 jeux de données ventes/analyses)
│   │   ├── 01_donnees_vente.csv
│   │   ├── 02_analyse_region.csv
│   │   ├── 03_analyse_categorie.csv
│   │   ├── 04_analyse_canaux.csv
│   │   └── 05_kpis_globaux.csv
│
├── documents/                    # Guides RAG (Markdown)
│   └── *.md
│
├── backend/
│   ├── main.py                   # Point d'entrée FastAPI
│   ├── config.py                 # Configuration globale
│   │
│   ├── analysis/                 # Analyseurs de données
│   │   ├── loader.py
│   │   ├── kpis_analyzer.py
│   │   ├── canaux_analyzer.py
│   │   ├── categories_analyzer.py
│   │   └── anomaly_detector.py
│   │
│   ├── agents/                   # Agents LangGraph (5 agents)
│   │   ├── state.py              # État partagé TypedDict
│   │   ├── graph.py              # Graphe LangGraph
│   │   ├── analysis_agent.py     # Calcul des KPIs
│   │   ├── interpretation_agent.py # Interprétation LLM
│   │   ├── rag_agent.py          # Recherche dans les guides
│   │   ├── recommendation_agent.py # Génération recommandations
│   │   └── report_agent.py       # Structuration rapport
│   │
│   ├── rag/                      # Système RAG
│   │   ├── embeddings.py         # sentence-t5-base
│   │   ├── ingest.py             # Ingestion documents
│   │   ├── retriever.py          # Recherche ChromaDB
│   │   └── chroma_db/            # Base vectorielle
│   │
│   ├── models/                   # Schémas Pydantic
│   │   ├── request_models.py
│   │   └── response_models.py
│   │
    ├── sql_agent/               # Agent SQL (exploration données)
    │   ├── db.py                 # DuckDB — 5 CSV comme tables SQL
    │   ├── validator.py          # Sécurité : SELECT only, mots-clés interdits
    │   ├── generator.py          # DeepSeek : NL → SQL + viz_type
    │   ├── executor.py           # Exécution async, timeout 10s, max 500 lignes
    │   └── intent_router.py      # Classifie : "sql" ou "strategic"
    │
    ├── routes/                   # Routes API
    │   ├── analyze.py            # POST /analyze
    │   ├── upload.py             # POST /upload
    │   ├── chat.py               # POST /chat (SSE + intent routing)
    │   ├── report.py             # GET /report
    │   └── sql.py                # POST /sql/query, POST /sql/query/export
    │
    └── tests/                    # Tests unitaires et d'intégration
        ├── conftest.py           # Fixtures partagées
        ├── test_analysis.py      # 38 tests — analyzers + anomaly detector
        ├── test_agents.py        # 16 tests — agents LangGraph
        ├── test_rag.py           # 15 tests — retriever ChromaDB
        ├── test_routes.py        # 16 tests — routes FastAPI
        ├── test_sql_agent.py     # 20 tests — validator, intent_router, executor, route
        └── test_results.txt      # Rapport généré par run_tests.ps1
│
└── frontend/
    ├── .env                      # VITE_API_URL
    ├── package.json
    ├── vite.config.js
    ├── tailwind.config.js
    ├── index.html
    │
    └── src/
        ├── main.jsx              # Point d'entrée
        ├── App.jsx               # Router + Navbar
        ├── index.css             # Tailwind imports
        │
        ├── services/             # Appels API
        │   ├── api.js            # Instance Axios
        │   ├── uploadService.js
        │   └── chatService.js    # Streaming SSE
        │
        ├── hooks/                # Hooks React
        │   ├── useChat.js
        │   └── useAnalysis.js
        │
        ├── components/           # Composants UI
        │   ├── KpiCard.jsx
        │   ├── ChatMessage.jsx
        │   ├── FileUploader.jsx
        │   ├── AgentProgress.jsx
        │   ├── Charts.jsx
        │   └── SqlResult.jsx     # Tableau + graphique Recharts pour résultats SQL
        │
        └── pages/                # Pages
            ├── Dashboard.jsx     # Grille KPIs + graphiques
            ├── Upload.jsx        # Upload CSV
            ├── Chat.jsx          # Interface chat
            └── Report.jsx        # Rapport complet
```

---

## Commandes Résumé

| Action | Commande |
|--------|----------|
| Installer dépendances Python | `pip install -r requirements.txt` |
| Installer dépendances JS | `cd frontend && npm install` |
| Indexer les documents | `python -m backend.rag.ingest` |
| Lancer le backend | `uvicorn backend.main:app --reload --port 8000` |
| Lancer le frontend | `cd frontend && npm run dev` |
| Tester l'API | `curl -X POST http://localhost:8000/analyze` |
| **Tester le SQL agent** | `curl -X POST http://localhost:8000/sql/query -H "Content-Type: application/json" -d '{"question": "Top 5 campagnes"}'` |
| **Lancer les tests** | `.venv\Scripts\python.exe -m pytest backend/tests/ -v` |
| **Tests SQL uniquement** | `.venv\Scripts\python.exe -m pytest backend/tests/test_sql_agent.py -v` |
| **Tests + rapport fichier** | `.\run_tests.ps1` |

---

## Pages Frontend

| Page | Route | Description |
|------|-------|-------------|
| Dashboard | `/` | Grille des KPIs, graphiques Recharts |
| Upload | `/upload` | Drag-and-drop CSV avec validation |
| Chat | `/chat` | Interface conversationnelle avec streaming |
| Report | `/report` | Rapport complet avec recommandations |

---

## Phases de Développement

- [x] **Phase 1** : Configuration (config.py, loader.py)
- [x] **Phase 2** : Analyzers + Analysis Agent + route /analyze
- [x] **Phase 3** : Système RAG complet + RAG Agent
- [x] **Phase 4** : Interpretation + Recommendation + Report Agents + Frontend React
- [x] **Phase 5** : Tests unitaires et d'intégration — 85/85 tests passés
- [x] **Phase 6** : SQL Agent — exploration données en langage naturel (DuckDB + intent routing)

---

## Tests

```bash
# Lancer tous les tests
.venv\Scripts\python.exe -m pytest backend/tests/ -v

# Lancer les tests avec rapport sauvegardé dans backend/tests/test_results.txt
.\run_tests.ps1
```

| Fichier | Tests | Couverture |
|---------|-------|------------|
| `test_analysis.py` | 38 | FinanceAnalyzer, MarketingAnalyzer, SupportAnalyzer, AnomalyDetector |
| `test_agents.py` | 16 | create_initial_state, analysis_agent, pipeline mocké |
| `test_rag.py` | 15 | structure résultats, pertinence, robustesse |
| `test_routes.py` | 16 | /health, /upload, /analyze, /report |
| `test_sql_agent.py` | 20 | validate_sql, enforce_limit, classify_intent, execute_sql, POST /sql/query |
| **Total** | **105** | **105/105 PASSED** |

---

## Auteur

Projet PFE — AI Business Consultant pour PME tunisiennes.
