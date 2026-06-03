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
│   │   ├── 01_donnees_vente.csv
│   │   ├── 02_analyse_region.csv
│   │   ├── 03_analyse_categorie.csv
│   │   ├── 04_analyse_canaux.csv
│   │   └── 05_kpis_globaux.csv
│   └── last_report.json
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
    │   ├── loader.py               # chargement + validation + nettoyage des 5 CSV
    │   ├── kpis_analyzer.py        # KPIs financiers globaux (05_kpis_globaux.csv)
    │   ├── canaux_analyzer.py      # KPIs canaux de vente (04_analyse_canaux.csv)
    │   ├── categories_analyzer.py  # KPIs catégories produits (03_analyse_categorie.csv)
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
    │   ├── db.py                   # DuckDB in-memory, 5 CSV comme tables
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

Les 5 fichiers sont chargés depuis `data/uploads/` via `loader.py`.
Les clés dans `raw_data` (état LangGraph) : `"ventes"`, `"regions"`, `"categories"`, `"canaux"`, `"kpis"`.

### 01_donnees_vente.csv — Transactions individuelles
```
invoice_id       : string  → identifiant unique de la facture (ex: INV00001)
product_name     : string  → nom du produit vendu
category         : string  → catégorie (Mobilier, Electronique, Fournitures, Divers…)
quantity         : int     → quantité vendue
unit_price_tnd   : float   → prix unitaire (TND)
revenue_tnd      : float   → chiffre d'affaires = quantity × unit_price_tnd (TND)
customer_id      : string  → identifiant client (ex: CUS1356)
customer_region  : string  → région (Tunis, Ariana, Sfax, Sousse…)
sale_date        : string  → date de vente, format YYYY-MM-DD
sales_channel    : string  → canal (Magasin physique, Site Web, Téléphone…)
payment_method   : string  → moyen de paiement (Carte bancaire, Especes, Virement…)
estimated_profit : float   → profit estimé (TND)
```

### 02_analyse_region.csv — Agrégation par région géographique
```
customer_region  : string  → région tunisienne (Tunis, Ariana, Sfax…)
CA_Total         : float   → chiffre d'affaires total de la région (TND)
Profit_Total     : float   → profit total de la région (TND)
Nb_Transactions  : int     → nombre de transactions dans la région
Panier_Moyen     : float   → panier moyen = CA_Total / Nb_Transactions (TND)
```

### 03_analyse_categorie.csv — Agrégation par catégorie de produit
```
category         : string  → catégorie de produit
CA_Total         : float   → chiffre d'affaires total de la catégorie (TND)
Profit_Total     : float   → profit total de la catégorie (TND)
Nb_Transactions  : int     → nombre de transactions
Quantite_Vendue  : int     → quantité totale vendue
Prix_Moyen       : float   → prix moyen par unité (TND)
```

### 04_analyse_canaux.csv — Agrégation par canal de vente
```
sales_channel    : string  → canal de vente (Site Web, Magasin Physique…)
ca_total         : float   → chiffre d'affaires total du canal (TND)
nb_transactions  : int     → nombre de transactions par canal
panier_moyen     : float   → panier moyen par canal (TND)
```

### 05_kpis_globaux.csv — KPIs globaux (format clé-valeur)
```
indicateur       : string  → nom de l'indicateur (ex: "CA Total (TND)")
valeur           : float   → valeur numérique de l'indicateur

Indicateurs présents :
  CA Total (TND)             → chiffre d'affaires global
  Profit Total (TND)         → profit global
  Marge Beneficiaire (%)     → marge bénéficiaire moyenne
  Nb Transactions            → nombre total de transactions
  Panier Moyen (TND)         → panier moyen global
  Quantite Totale Vendue     → quantité totale vendue
  Nb Clients Uniques         → nombre de clients distincts
  CA Moyen par Client (TND)  → CA moyen par client
```

---

## 6. État partagé LangGraph (agents/state.py)

L'état est un `TypedDict` qui circule entre tous les agents.
Chaque agent lit l'état, le complète, et le passe au suivant.

```python
# Structure de référence — à implémenter dans agents/state.py
class AgentState(TypedDict):
    # Entrée
    raw_data: Dict[str, Any]        # DataFrames sérialisés des 5 CSV
                                    # clés : "ventes", "regions", "categories", "canaux", "kpis"
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

### KPIs financiers globaux (kpis_analyzer.py) — source : 05_kpis_globaux.csv
- `revenue_total` : chiffre d'affaires global (TND)
- `profit_total` : profit global (TND)
- `profit_margin` : marge bénéficiaire (%)
- `nb_transactions` : nombre total de transactions
- `panier_moyen` : panier moyen global (TND)
- `quantite_totale` : quantité totale vendue
- `nb_clients` : nombre de clients uniques
- `ca_moyen_client` : CA moyen par client (TND)

### KPIs canaux de vente (canaux_analyzer.py) — source : 04_analyse_canaux.csv
- `total_ca` : CA total tous canaux confondus (TND)
- `total_transactions` : nombre total de transactions
- `best_channel` : canal avec le plus fort CA
- `top_panier_channel` : canal avec le panier moyen le plus élevé
- `ca_by_channel` : CA par canal (dict)
- `transactions_by_channel` : transactions par canal (dict)
- `panier_by_channel` : panier moyen par canal (dict)

### KPIs catégories produits (categories_analyzer.py) — source : 03_analyse_categorie.csv
- `total_revenue` : CA total toutes catégories (TND)
- `total_profit` : profit total toutes catégories (TND)
- `total_transactions` : nombre total de transactions
- `total_quantity` : quantité totale vendue
- `top_category_by_revenue` : catégorie avec le plus fort CA
- `top_category_by_quantity` : catégorie avec la plus grande quantité vendue
- `revenue_by_category` : CA par catégorie (dict)
- `profit_by_category` : profit par catégorie (dict)
- `qty_by_category` : quantité vendue par catégorie (dict)

> Note : `01_donnees_vente.csv` et `02_analyse_region.csv` sont disponibles dans
> `raw_data` pour l'agent SQL (DuckDB) mais ne font pas l'objet d'un analyzer dédié.

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
    Calcule les KPIs financiers globaux, canaux et catégories produits.
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
- **Marché :** contexte PME tunisienne du secteur retail/commerce — ventes multi-canaux
  (magasin physique, site web, téléphone), produits : Mobilier, Electronique, Fournitures
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
