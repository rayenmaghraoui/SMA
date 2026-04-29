# AI Business Consultant — Système Multi-Agents

Projet de Fin d'Études (PFE) — Système d'aide à la décision pour PME tunisiennes.

## Description

Ce système analyse les données opérationnelles d'entreprises tunisiennes (finance, marketing, support client), détecte les problèmes de gestion et produit des recommandations stratégiques adaptées au contexte local.

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

**Pipeline complet des 5 agents :**
```
analysis_agent → interpretation_agent → rag_agent → recommendation_agent → report_agent → END
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

**4.1 — Fichiers CSV (dans `data/`)**

Tu dois avoir ces 3 fichiers :
```
data/
├── 01_finance_performance.csv
├── 02_marketing_campaigns.csv
└── 03_customer_support.csv
```

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
    "finance": { "revenue_total": 1250000, "profit_margin": 15.2, "trend": "hausse" },
    "marketing": { "avg_conversion_rate": 4.5, "best_channel": "social_media" },
    "support": { "avg_satisfaction": 3.8, "sla_compliance": 85.0 }
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

Interface conversationnelle avec streaming SSE.

```bash
curl -X POST -H "Content-Type: application/json" \
  -d '{"message": "Analysez les performances financières"}' \
  http://localhost:8000/chat
```

**Format SSE :**
```
data: {"type": "step", "content": "Analyse des données en cours..."}
data: {"type": "token", "content": "Voici "}
data: {"type": "token", "content": "mon "}
data: {"type": "token", "content": "analyse..."}
data: {"type": "done", "content": ""}
```

### GET /report

Récupère le dernier rapport généré.

```bash
curl http://localhost:8000/report
```

### GET /health

Vérifie l'état de l'API et d'Ollama.

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
│   ├── uploads/                  # Fichiers uploadés
│   ├── 01_finance_performance.csv
│   ├── 02_marketing_campaigns.csv
│   └── 03_customer_support.csv
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
│   │   ├── finance_analyzer.py
│   │   ├── marketing_analyzer.py
│   │   ├── support_analyzer.py
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
│   └── routes/                   # Routes API
│       ├── analyze.py            # POST /analyze
│       ├── upload.py             # POST /upload
│       ├── chat.py               # POST /chat (SSE)
│       └── report.py             # GET /report
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
        │   └── Charts.jsx
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
| Lancer Ollama | `ollama serve` |
| Télécharger Mistral | `ollama pull mistral` |
| Indexer les documents | `python -m backend.rag.ingest` |
| Lancer le backend | `uvicorn backend.main:app --reload --port 8000` |
| Lancer le frontend | `cd frontend && npm run dev` |
| Tester l'API | `curl -X POST http://localhost:8000/analyze` |

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

---

## Auteur

Projet PFE — AI Business Consultant pour PME tunisiennes.
