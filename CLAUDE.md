# CLAUDE.md — AI Business Consultant (PFE)
# Lis ce fichier en entier avant de générer du code.

---

## 1. Présentation du projet

**Nom :** AI Business Consultant
**Type :** Projet de Fin d'Études (PFE) — Système multi-agents d'aide à la décision
**Objectif :** Analyser les données opérationnelles d'entreprises tunisiennes, détecter
les problèmes de gestion et produire des recommandations stratégiques adaptées au
contexte économique et réglementaire local (Tunisie).

**Utilisateur cible :** Dirigeants et managers de PME tunisiennes.
**Langue des réponses IA :** Français (les recommandations sont en français).
**Langue du code :** Anglais (noms de variables, fonctions, classes).
**Langue des commentaires :** Français.

---

## 2. Architecture générale

```
Utilisateur
    │
    ▼
Frontend (React)
    │  REST + SSE streaming
    ▼
Backend (FastAPI)
    │
    ├── Intent Router ──────────────────────────────────────────┐
    │         │                                                  │
    │    ["sql"]                                          ["strategic"]
    │         │                                                  │
    │         ▼                                                  ▼
    │   SQL Agent (DuckDB)                      Multi-Agents Pipeline (LangGraph)
    │         │                                          │
    │  NL → SQL (DeepSeek)                  ├── Analysis Agent
    │  validate → execute                   ├── Interpretation Agent
    │  tableau + graphique                  ├── RAG Agent
    │                                       ├── Recommendation Agent
    │                                       └── Report Agent
    │                                                  │
    │                                       ├── Data Analysis (Pandas + Scikit-learn)
    │                                       ├── RAG System (ChromaDB + sentence-t5-base)
    │                                       └── LLM (DeepSeek-V3.2 via Azure AI Foundry)
```

**Workflow stratégique (questions d'analyse) :**
```
input_data → analysis_agent → interpretation_agent → rag_agent
           → recommendation_agent → report_agent → final_output
```

**Workflow SQL (questions de données) :**
```
question → intent_router → generate_sql (DeepSeek) → validate_sql
         → execute_sql (DuckDB) → chart_data → SqlResult (frontend)
```

---

## 3. Stack technique complète

### Backend
| Composant         | Technologie                            | Version  |
|-------------------|----------------------------------------|----------|
| API               | FastAPI                                | 0.110+   |
| Serveur           | Uvicorn                                | dernière |
| Agents            | LangGraph                              | 0.2+     |
| LLM orchestration | LangChain                              | 0.3+     |
| Data analysis     | Pandas + NumPy + Scikit-learn          | dernière |
| Vector DB         | ChromaDB                               | 0.5+     |
| Embeddings        | sentence-transformers/sentence-t5-base | dernière |
| LLM cloud         | DeepSeek-V3.2 via Azure AI Foundry     | dernière |
| SQL In-Memory     | DuckDB                                 | 0.10+    |
| Validation        | Pydantic v2                            | 2.x      |
| Variables env     | python-dotenv                          | dernière |
| Tests             | pytest + pytest-asyncio                | dernière |

### Frontend
| Composant   | Technologie       |
|-------------|-------------------|
| Framework   | React 18          |
| Build tool  | Vite              |
| Styling     | Tailwind CSS v3   |
| Animations  | Framer Motion     |
| Graphiques  | Recharts          |
| HTTP client | Axios             |
| Streaming   | EventSource (SSE) |
| Routing     | React Router v6   |

### LLM & Embeddings
- **LLM :** `DeepSeek-V3.2` via Azure AI Foundry — variable `AZURE_OPENAI_ENDPOINT`
- **Modèle embeddings :** `sentence-transformers/sentence-t5-base`
  (T5 encoder fine-tuné pour la similarité sémantique — recommandé par l'encadrant)
- **Température LLM :** 0.3 (réponses cohérentes, peu aléatoires)
- **Max tokens :** 2048 pour les recommandations, 4096 pour le rapport final

---

## 4. Structure complète des dossiers

```
ai-business-consultant/
├── .env                            # variables d'environnement
├── requirements.txt                # dépendances Python
├── README.md                       # documentation
├── CLAUDE.md                       # ce fichier
│
├── data/                           # données
│   ├── uploads/                    # fichiers uploadés par l'utilisateur
│   ├── 01_finance_performance.csv
│   ├── 02_marketing_campaigns.csv
│   └── 03_customer_support.csv
│
├── documents/                      # base de connaissances RAG
│   ├── guide_gestion_entreprises_tunisiennes.md
│   ├── guide_gestion_financiere_tunisie.md
│   ├── guide_interpretation_kpis_tunisie.md
│   ├── guide_logistique_supply_chain_tunisie.md
│   └── guide_rh_droit_travail_tunisie.md
│
└── backend/
    ├── main.py                     # point d'entrée FastAPI
    ├── config.py                   # configuration globale (chemins, constantes)
    │
    ├── agents/                     # système multi-agents LangGraph
    │   ├── __init__.py
    │   ├── state.py                # TypedDict : état partagé entre tous les agents
    │   ├── graph.py                # graphe LangGraph : assemble les 5 nœuds
    │   ├── analysis_agent.py       # agent 1 : calcul KPIs + détection anomalies
    │   ├── interpretation_agent.py # agent 2 : interprétation LLM des KPIs
    │   ├── rag_agent.py            # agent 3 : recherche dans les guides tunisiens
    │   ├── recommendation_agent.py # agent 4 : génération recommandations
    │   └── report_agent.py         # agent 5 : structuration rapport final
    │
    ├── rag/                        # système RAG
    │   ├── __init__.py
    │   ├── embeddings.py           # config sentence-t5-base
    │   ├── ingest.py               # ingestion des 5 guides → ChromaDB
    │   ├── retriever.py            # recherche de similarité dans ChromaDB
    │   └── chroma_db/              # base vectorielle (générée automatiquement)
    │
    ├── analysis/                   # analyse des données
    │   ├── __init__.py
    │   ├── loader.py               # chargement + validation + nettoyage des CSV
    │   ├── finance_analyzer.py     # KPIs financiers
    │   ├── marketing_analyzer.py   # KPIs marketing
    │   ├── support_analyzer.py     # KPIs support client
    │   └── anomaly_detector.py     # détection anomalies (méthode IQR)
    │
    ├── routes/                     # endpoints FastAPI
    │   ├── __init__.py
    │   ├── upload.py               # POST /upload
    │   ├── chat.py                 # POST /chat  (SSE streaming + intent routing)
    │   ├── analyze.py              # POST /analyze
    │   ├── report.py               # GET /report
    │   └── sql.py                  # POST /sql/query, POST /sql/query/export
    │
    ├── sql_agent/                  # agent SQL — exploration données NL→SQL
    │   ├── __init__.py
    │   ├── db.py                   # DuckDB in-memory, 3 CSV comme tables
    │   ├── validator.py            # sécurité : SELECT only, mots-clés interdits
    │   ├── generator.py            # DeepSeek NL→SQL + viz_type
    │   ├── executor.py             # exécution async, timeout 10s, max 500 lignes
    │   └── intent_router.py        # classifie "sql" ou "strategic"
    │
    ├── models/                     # schémas Pydantic
    │   ├── __init__.py
    │   ├── request_models.py       # schémas des requêtes entrantes
    │   ├── response_models.py      # schémas des réponses sortantes
    │   └── agent_state.py          # modèle Pydantic de l'état des agents
    │
    └── tests/                      # tests unitaires
        ├── test_analysis.py
        ├── test_rag.py
        ├── test_agents.py
        ├── test_routes.py
        └── test_sql_agent.py       # 20 tests : validator, intent_router, executor, route
```

---

## 5. Datasets — schéma exact des CSV

### 01_finance_performance.csv
```
date          : string  → format YYYY-MM-DD
revenue       : float   → chiffre d'affaires mensuel (TND)
cost          : float   → charges totales (TND)
profit        : float   → bénéfice net = revenue - cost (TND)
growth_rate   : float   → taux de croissance vs mois précédent (%)
```

### 02_marketing_campaigns.csv
```
date             : string  → format YYYY-MM-DD
campaign_id      : string  → identifiant unique de la campagne
channel          : string  → canal (social_media, email, SEO, display...)
budget           : float   → budget dépensé (TND)
clicks           : int     → nombre de clics
conversions      : int     → nombre de conversions
conversion_rate  : float   → taux de conversion = conversions/clicks (%)
```

### 03_customer_support.csv
```
date               : string  → format YYYY-MM-DD
ticket_id          : string  → identifiant unique du ticket
issue_type         : string  → type de problème (billing, technical, shipping...)
resolution_hours   : float   → temps de résolution en heures
satisfaction_score : float   → score satisfaction 1-5
churn_risk         : string  → niveau de risque (low, medium, high)
```

---

## 6. État partagé LangGraph (agents/state.py)

L'état est un `TypedDict` qui circule entre tous les agents.
Chaque agent lit l'état, le complète, et le passe au suivant.

```python
# Structure de référence — à implémenter dans agents/state.py
class AgentState(TypedDict):
    # Entrée
    raw_data: Dict[str, Any]        # DataFrames sérialisés des 3 CSV
    user_question: Optional[str]    # question posée via le chat

    # Résultats Analysis Agent
    kpis: Dict[str, Any]            # KPIs calculés par les 3 analyzers
    anomalies: List[Dict]           # anomalies détectées

    # Résultats Interpretation Agent
    interpretation: str             # analyse textuelle des KPIs par le LLM

    # Résultats RAG Agent
    rag_context: List[Dict]         # passages pertinents + sources

    # Résultats Recommendation Agent
    recommendations: List[Dict]     # liste de recommandations priorisées

    # Résultats Report Agent
    report: Dict[str, Any]          # rapport final structuré

    # Métadonnées
    errors: List[str]               # erreurs non bloquantes
    current_step: str               # étape en cours (pour le streaming)
```

---

## 7. KPIs calculés par domaine

### Finance (finance_analyzer.py)
- `revenue_total` : somme du chiffre d'affaires sur la période
- `profit_total` : somme des bénéfices
- `profit_margin` : marge bénéficiaire moyenne (%)
- `avg_growth_rate` : taux de croissance moyen (%)
- `best_month` : mois le plus rentable
- `worst_month` : mois le moins rentable
- `trend` : "hausse" | "baisse" | "stable" (basé sur régression linéaire)
- `revenue_volatility` : écart-type du revenue (mesure de stabilité)

### Marketing (marketing_analyzer.py)
- `total_budget_spent` : budget total dépensé (TND)
- `total_conversions` : nombre total de conversions
- `avg_conversion_rate` : taux de conversion moyen (%)
- `best_channel` : canal avec le meilleur ROI
- `roi_by_channel` : ROI par canal = conversions/budget × 100
- `cost_per_conversion` : coût moyen par conversion
- `top_campaign` : campagne la plus performante

### Support client (support_analyzer.py)
- `avg_satisfaction` : score de satisfaction moyen (1-5)
- `avg_resolution_hours` : temps moyen de résolution (heures)
- `high_churn_rate` : % de tickets avec churn_risk = "high"
- `top_issue_type` : type de problème le plus fréquent
- `sla_compliance` : % tickets résolus en moins de 24h
- `satisfaction_trend` : évolution de la satisfaction dans le temps

---

## 8. Routes API

| Méthode | Route               | Description                                      | Body / Params              |
|---------|---------------------|--------------------------------------------------|----------------------------|
| POST    | /upload             | Upload un fichier CSV                            | multipart/form-data        |
| POST    | /analyze            | Lance le pipeline complet sur les données        | `{ "use_defaults": bool }` |
| POST    | /chat               | Question en langage naturel (SSE stream)         | `{ "message": string }`    |
| GET     | /report             | Récupère le dernier rapport généré               | —                          |
| GET     | /health             | Vérifie que l'API est up                         | —                          |
| POST    | /sql/query          | Exploration données : NL → SQL → DuckDB → JSON   | `{ "question": string }`   |
| POST    | /sql/query/export   | Idem mais retourne un fichier CSV téléchargeable | `{ "question": string }`   |

**Format SSE pour /chat — question stratégique :**
```
data: {"type": "step",  "content": "Analyse des données en cours..."}
data: {"type": "token", "content": "Insight 1: La marge "}
data: {"type": "token", "content": "bénéficiaire est ..."}
data: {"type": "report", "content": "{...}"}
data: {"type": "done",  "content": ""}
```

**Format SSE pour /chat — question SQL :**
```
data: {"type": "sql_result", "content": "{sql, rows_preview, total_rows, chart_data, message}"}
data: {"type": "done",  "content": ""}
```

**Streaming :** les tokens sont envoyés par blocs de 60 caractères (préserve les sauts de ligne et la structure Markdown).

**Format de réponse du chat (interpretation_agent) :**
```
Insight 1: courte explication
Insight 2: courte explication
Insight 3: courte explication
Action 1: courte recommandation
Action 2: courte recommandation
```
Règles : max 5 points, 1 phrase par point, pas de gras ni de symboles Markdown.

---

## 9. Configuration (.env)

```bash
# LLM (Azure AI Foundry — DeepSeek-V3.2)
AZURE_OPENAI_API_KEY=<votre_clé>
AZURE_OPENAI_ENDPOINT=https://<ressource>.services.ai.azure.com/openai/v1/
AZURE_OPENAI_MODEL=DeepSeek-V3.2
LLM_TEMPERATURE=0.3
LLM_MAX_TOKENS=2048

# Embeddings — sentence-T5-base (recommandé par l'encadrant)
EMBEDDING_MODEL=sentence-transformers/sentence-t5-base

# Chemins
DATA_DIR=./data
DOCUMENTS_DIR=./documents
CHROMA_DB_PATH=./backend/rag/chroma_db
UPLOADS_DIR=./data/uploads

# RAG — stratégie d'indexation hybride
RAG_CHUNK_SIZE=500
RAG_CHUNK_OVERLAP=50
RAG_TOP_K=3

# API
API_HOST=0.0.0.0
API_PORT=8000
FRONTEND_URL=http://localhost:5173

# Environnement
DEBUG=true
```

---

## 10. RAG — Stratégie d'indexation et embeddings

### Modèle d'embeddings
```
Modèle   : sentence-transformers/sentence-t5-base
Pourquoi : T5 encoder fine-tuné pour la similarité sémantique.
           Produit des embeddings plus denses et mieux séparés
           que MiniLM. Recommandé par l'encadrant. Académiquement
           rigoureux à défendre devant un jury PFE.
Config   : normalize_embeddings=True · device=cpu · batch_size=32
Dimension: 768
Max tokens par chunk : 512 (limite du modèle — ne pas dépasser)
```

### Stratégie de chunking — deux passes
```
Passe 1 — MarkdownHeaderTextSplitter
  Objectif : découper par section logique du document
  Config   : headers_to_split_on=[
               ("#",   "titre"),
               ("##",  "section"),
               ("###", "sous_section")
             ]
  Résultat : chaque chunk parle d'un seul sujet cohérent

Passe 2 — RecursiveCharacterTextSplitter
  Objectif : re-découper les sections trop longues
  Config   : chunk_size=500 · chunk_overlap=50
             separators=["\n\n", "\n", ". ", " "]
  Résultat : aucun chunk ne dépasse 512 tokens (limite T5)
```

### Métadonnées stockées par chunk
```python
{
  "page_content": "...",
  "metadata": {
    "titre":        "Guide de gestion financière",
    "section":      "Fiscalité et TVA",
    "sous_section": "Taux applicables",
    "source":       "guide_gestion_financiere_tunisie.md"
  }
}
```

### Recherche (retriever.py)
```
Méthode : similarité cosinus
Top-k   : 3 chunks par requête
DB      : ChromaDB (stockage local → backend/rag/chroma_db/)
```

### Phrase de référence pour le rapport PFE
> "Nous utilisons sentence-T5-base pour la génération d'embeddings
>  sémantiques, combiné à une stratégie d'indexation hybride
>  Markdown-Header + Recursive Splitting, stockée dans ChromaDB
>  avec similarité cosinus."

---

## 11. Conventions de code

### Python
- **Type hints** obligatoires sur toutes les fonctions
- **Docstrings** en français sur toutes les classes et fonctions publiques
- **Async/await** pour toutes les routes FastAPI et les appels LLM
- **Logging** avec le module `logging` standard (pas de print en production)
- **Gestion d'erreurs** : try/except sur tous les appels externes
- **Retour des agents** : toujours retourner l'état complet mis à jour

```python
# Exemple de convention pour un agent
async def analysis_agent(state: AgentState) -> AgentState:
    """
    Agent d'analyse des données.
    Calcule les KPIs financiers, marketing et support client.
    """
    try:
        # ... logique
        return {**state, "kpis": kpis, "anomalies": anomalies}
    except Exception as e:
        logger.error(f"Erreur analysis_agent: {e}")
        return {**state, "errors": state["errors"] + [str(e)]}
```

### React / JavaScript
- **Composants fonctionnels** uniquement (pas de classes)
- **Hooks custom** pour toute logique réutilisable
- **Tailwind** pour le styling (pas de CSS inline sauf exceptions)
- **Gestion d'erreurs** : afficher un message clair à l'utilisateur

---

## 12. Contexte tunisien — points importants pour le LLM

Quand tu génères les prompts système pour les agents LLM, tiens compte de :

- **Monnaie :** Dinar Tunisien (TND) — ne pas utiliser EUR ou USD
- **Réglementation :** Code du travail tunisien, loi 2016-71 sur l'investissement
- **Fiscalité :** TVA 19%, IS 15% pour les PME (taux standard)
- **Marché :** contexte PME tunisienne, secteurs dominants (tourisme, textile, agro)
- **Langue :** recommandations en français, termes techniques acceptés en anglais
- **Saisonnalité :** tenir compte du mois de Ramadan dans les analyses marketing
- **BFPME / SOTUGAR :** organismes de financement locaux à mentionner si pertinent

---

## 13. Commandes utiles

```bash
# Installer les dépendances Python
pip install -r requirements.txt

# Ingérer les documents RAG (à faire une seule fois)
cd backend
python -m rag.ingest

# Lancer le backend
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000

# Lancer le frontend
cd frontend
npm install
npm run dev

# Lancer les tests
pytest backend/tests/ -v
```

---

## 14. Ordre de développement recommandé

```
Phase 1 (Semaine 1-2) : config.py → loader.py → tests données
Phase 2 (Semaine 3-4) : *_analyzer.py → anomaly_detector.py
                         → state.py → analysis_agent.py
                         → graph.py (1 nœud) → routes/analyze.py → main.py
Phase 3 (Semaine 5-6) : embeddings.py (sentence-t5-base)
                         → ingest.py (MD header + recursive splitting)
                         → retriever.py → rag_agent.py
                         → graph.py (2 nœuds)
Phase 4 (Semaine 7-9) : interpretation_agent.py → recommendation_agent.py
                         → report_agent.py → graph.py (5 nœuds complets)
                         → routes/chat.py → routes/upload.py → routes/report.py
                         → frontend complet
```

---

## 15. Ce que tu NE dois PAS faire

- Ne pas utiliser `print()` en dehors des scripts de test — utiliser `logging`
- Ne pas hardcoder les chemins de fichiers — utiliser `config.py`
- Ne pas appeler l'API Azure de façon synchrone — toujours `async/await`
- Ne pas stocker les DataFrames bruts dans l'état LangGraph — les sérialiser en dict
- Ne pas générer de code frontend sans Tailwind CSS
- Ne pas oublier les CORS dans `main.py` (le frontend est sur le port 5173)
- Ne pas dépasser 512 tokens par chunk (limite du modèle sentence-t5-base)
- Ne pas changer le modèle d'embeddings sans re-ingérer tous les documents
- Ne pas créer de nouveaux fichiers hors de la structure définie en section 4
  sans le mentionner explicitement
