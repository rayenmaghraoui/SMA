# Explication Détaillée du Projet PFE : AI Business Consultant pour PME Tunisiennes

Ce document a pour but de clarifier et de vulgariser l'ensemble du travail réalisé dans le cadre de ce Projet de Fin d'Études (PFE). Il est rédigé de manière à mettre en évidence la valeur ajoutée scientifique et technique du projet.

---

## 1. Le Sujet du Projet (La Problématique)

**Le constat :** Les Petites et Moyennes Entreprises (PME) tunisiennes génèrent énormément de données (cinq datasets CSV : ventes, régions, catégories, canaux, KPIs globaux) mais manquent souvent d'expertise, de temps ou de budget pour engager des consultants en stratégie d'entreprise afin d'analyser ces données et de prendre les bonnes décisions.

**La solution proposée :** J'ai développé un **"Consultant d'Entreprise IA" (AI Business Consultant)**. C'est un système intelligent autonome capable de :
1. Lire et comprendre les données brutes de l'entreprise.
2. Détecter les anomalies ou les baisses de performance.
3. Croiser ces données avec le contexte juridique et économique tunisien.
4. Fournir un rapport stratégique avec des recommandations concrètes, exactement comme le ferait un consultant humain.

---

## 1.5. Schéma Global de l'Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        UTILISATEUR (Manager PME)                     │
└───────────────────────────────┬─────────────────────────────────────┘
                                │  Navigateur Web
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    FRONTEND  (React 18 + Vite)                       │
│                                                                      │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────┐  ┌───────────┐  │
│  │  Dashboard   │  │    Upload    │  │   Chat    │  │  Report   │  │
│  │  KPI+Charts  │  │  CSV Files   │  │  SSE Live │  │  Rapport  │  │
│  └──────────────┘  └──────────────┘  └───────────┘  └───────────┘  │
│         Tailwind CSS · Recharts · Framer Motion · Axios             │
└───────────────────────────────┬─────────────────────────────────────┘
                                │  REST + SSE (port 5173 → 8000)
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    BACKEND  (FastAPI + Uvicorn)                      │
│                                                                      │
│  POST /upload   POST /analyze   POST /chat (SSE)   GET /report      │
│  GET /health                                                         │
│                     Pydantic v2 · CORS · Async                      │
└───────────────────────────────┬─────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│              PIPELINE MULTI-AGENTS  (LangGraph)                      │
│                                                                      │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐             │
│  │  Analysis   │───▶│Interpretation│───▶│  RAG Agent  │             │
│  │   Agent     │    │   Agent     │    │             │             │
│  │  (sync)     │    │  (LLM call) │    │ (ChromaDB)  │             │
│  └─────────────┘    └─────────────┘    └──────┬──────┘             │
│        │                  │                   │                     │
│        ▼                  ▼                   ▼                     │
│  ┌──────────────────────────────────────────────────┐              │
│  │              ÉTAT PARTAGÉ (AgentState)            │              │
│  │  raw_data · kpis · anomalies · interpretation    │              │
│  │  rag_context · recommendations · report · errors │              │
│  └──────────────────────────────────────────────────┘              │
│                                                                      │
│                   ┌─────────────┐    ┌─────────────┐               │
│                   │Recommendation│───▶│   Report    │               │
│                   │   Agent     │    │   Agent     │               │
│                   │  (LLM call) │    │  (LLM call) │               │
│                   └─────────────┘    └─────────────┘               │
└──────────────┬──────────────────────────────┬───────────────────────┘
               │                              │
               ▼                              ▼
┌──────────────────────────┐    ┌─────────────────────────────────────┐
│   ANALYSE DE DONNÉES     │    │       SYSTÈME RAG                   │
│                          │    │                                     │
│  Pandas · NumPy          │    │  sentence-t5-base (embeddings 768d) │
│  Scikit-learn (régress.) │    │  ChromaDB (similarité cosinus)      │
│  IQR anomaly detection   │    │  Chunking Markdown + Recursive      │
│                          │    │  5 guides tunisiens indexés         │
│  KPIs Finance            │    │  (fiscalité, RH, logistique...)     │
│  KPIs Canaux de vente    │    │                                     │
│  KPIs Catégories         │    └────────────────┬────────────────────┘
└──────────────────────────┘                     │
                                                 ▼
                                ┌─────────────────────────────────────┐
                                │   LLM CLOUD                         │
                                │   DeepSeek-V3.2                     │
                                │   via Azure AI Foundry              │
                                │   température 0.3 · max 2048 tokens │
                                └─────────────────────────────────────┘
```

---

## 2. Le Travail Réalisé (Mes Contributions)

Au lieu de faire une simple application web, j'ai construit une véritable architecture d'Intelligence Artificielle de niveau production. Mon travail s'est divisé en plusieurs axes majeurs :

*   **Ingénierie de la Donnée (Data Science) :**
    *   Création de scripts d'analyse de données avec Pandas et Numpy.
    *   Utilisation de modèles de Machine Learning (Scikit-learn) pour calculer les KPIs (Indicateurs Clés de Performance) et détecter des anomalies statistiques dans les données de l'entreprise.
*   **Création d'un Système Multi-Agents (LangGraph) :**
    *   C'est le cœur de mon travail. Plutôt que de poser une question à une IA "stupide", j'ai créé **5 agents IA spécialisés** qui collaborent entre eux (voir section 3).
*   **Mise en place d'un système RAG (Retrieval-Augmented Generation) :**
    *   Pour que l'IA ne donne pas des conseils génériques, j'ai créé une base de connaissances (ChromaDB) contenant des guides spécifiques au marché tunisien (lois, logistique, gestion).
    *   J'ai utilisé des modèles d'Embeddings (Sentence-T5) pour transformer ces documents en vecteurs mathématiques.
*   **Intégration d'un LLM via API (DeepSeek-V3.2 via Azure AI Foundry) :**
    *   J'ai intégré le modèle **DeepSeek-V3.2** accessible via **Azure AI Foundry** en utilisant `langchain-openai`. Cette approche offre une puissance de traitement linguistique élevée sans nécessiter de matériel local puissant.
*   **SQL Agent — Exploration de données en langage naturel :**
    *   En plus du pipeline stratégique, j'ai développé un agent SQL autonome. L'utilisateur peut poser des questions directes sur les données (ex: "Top 5 campagnes par conversions"), et le système génère automatiquement la requête SQL, l'exécute sur DuckDB, et affiche le résultat sous forme de tableau interactif + graphique Recharts.
*   **Développement Full-Stack et Déploiement :**
    *   Création d'une API backend robuste avec FastAPI.
    *   Développement d'une interface utilisateur (Frontend) moderne et interactive avec React 18 et Tailwind CSS.
    *   Dockerisation complète du projet (Docker-compose) pour garantir un déploiement facile sur n'importe quel serveur.

---

## 3. Comment fonctionne le Système Multi-Agents ? (L'Architecture des 5 Agents)

### Schéma du Pipeline

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                         ENTRÉE                                               │
│          5 CSV (ventes, régions, catégories, canaux, kpis) + Question Chat    │
└─────────────────────────────────┬────────────────────────────────────────────┘
                                  │
                                  ▼
         ┌────────────────────────────────────────┐
         │          AGENT 1 — Analysis Agent       │
         │  ● Pandas : charge et valide les CSV    │
         │  ● Calcule 20+ KPIs par domaine         │
         │  ● Scikit-learn : tendance (régression) │
         │  ● IQR : détecte les anomalies          │
         │                                         │
         │  Sorties → kpis, anomalies              │
         └────────────────────────────────────────┘
                                  │
                                  ▼
         ┌────────────────────────────────────────┐
         │       AGENT 2 — Interpretation Agent    │
         │  ● Construit un prompt dynamique avec   │
         │    les KPIs et anomalies calculés       │
         │  ● Appelle DeepSeek-V3.2 (Azure)        │
         │  ● Met des mots sur les chiffres        │
         │                                         │
         │  Sortie → interpretation (texte)        │
         └────────────────────────────────────────┘
                                  │
                                  ▼
         ┌────────────────────────────────────────┐
         │          AGENT 3 — RAG Agent            │
         │  ● Formule des requêtes sémantiques     │
         │  ● sentence-t5-base → vecteurs 768d     │
         │  ● Similarité cosinus dans ChromaDB     │
         │  ● Récupère Top-3 passages pertinents   │
         │    (lois tunisiennes, fiscalité, RH…)   │
         │                                         │
         │  Sortie → rag_context (passages+sources)│
         └────────────────────────────────────────┘
                                  │
                                  ▼
         ┌────────────────────────────────────────┐
         │      AGENT 4 — Recommendation Agent     │
         │  ● Fusionne : anomalies + interprétat.  │
         │    + contexte RAG tunisien              │
         │  ● Appelle DeepSeek-V3.2 (Azure)        │
         │  ● Produit N recommandations priorisées │
         │    (priorité haute/moyenne/faible)      │
         │                                         │
         │  Sortie → recommendations (liste JSON)  │
         └────────────────────────────────────────┘
                                  │
                                  ▼
         ┌────────────────────────────────────────┐
         │         AGENT 5 — Report Agent          │
         │  ● Assemble tous les résultats          │
         │  ● Structure le rapport JSON final      │
         │    (résumé exécutif, KPIs, anomalies,   │
         │    recommandations, sources RAG)        │
         │  ● Persiste dans data/last_report.json  │
         │                                         │
         │  Sortie → report (JSON complet)         │
         └────────────────────────────────────────┘
                                  │
                                  ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│                          SORTIE FINALE                                       │
│         Dashboard React · Chat SSE streaming · Rapport téléchargeable       │
└──────────────────────────────────────────────────────────────────────────────┘
```

La grande innovation de ce projet est l'utilisation de **LangGraph**. J'ai divisé le "cerveau" du consultant en 5 petits cerveaux (les agents), chacun ayant une tâche précise. Ils se passent l'information à la chaîne (Pipeline) :

1.  **Agent d'Analyse (Analysis Agent) :**
    *   *Son rôle :* C'est le statisticien. Il prend les fichiers CSV (Finance, Marketing, RH), calcule les chiffres (Revenus, marges, taux de conversion) et détecte mathématiquement ce qui ne va pas (ex: "Les ventes ont chuté de 15%").
2.  **Agent d'Interprétation (Interpretation Agent) :**
    *   *Son rôle :* C'est le manager. Il prend les chiffres froids de l'Agent 1, et demande au LLM d'expliquer *pourquoi* ces chiffres sont mauvais ou bons. Il met des mots sur les chiffres.
3.  **Agent Documentaire (RAG Agent) :**
    *   *Son rôle :* C'est l'expert juridique et marché local. En fonction des problèmes détectés par l'Agent 2, cet agent va fouiller dans la base de données vectorielle (ChromaDB) pour trouver des lois tunisiennes, des règles de fiscalité ou des normes logistiques qui pourraient expliquer le problème ou aider à le résoudre.
4.  **Agent de Recommandation (Recommendation Agent) :**
    *   *Son rôle :* C'est le consultant stratégique. Il prend les anomalies (Agent 1), les explications (Agent 2) et les lois tunisiennes (Agent 3) pour générer un plan d'action précis, étape par étape, pour le chef d'entreprise.
5.  **Agent de Rapport (Report Agent) :**
    *   *Son rôle :* C'est le secrétaire de direction. Il prend tout le travail des agents précédents et formate un rapport final propre, structuré (en format JSON/Markdown), prêt à être affiché sur le Dashboard React de l'utilisateur.

---

## 3.5. Précision Technique : Comment les agents ont-ils été codés (from scratch) ?

Il est important de souligner qu'aucun agent pré-configuré ou modèle tout prêt n'a été utilisé. L'intégralité du comportement des cinq agents a été programmée de A à Z en Python. Voici les grandes étapes de cette réalisation.

**La première brique est la définition de l'état partagé.** Tous les agents communiquent à travers un seul dictionnaire Python appelé `AgentState`, défini comme un `TypedDict`. Ce dictionnaire contient toutes les clés du pipeline : les données brutes en entrée (`raw_data`), les KPIs calculés (`kpis`), les anomalies détectées (`anomalies`), l'interprétation textuelle du LLM (`interpretation`), les passages RAG récupérés (`rag_context`), les recommandations priorisées (`recommendations`), le rapport final (`report`), ainsi que des métadonnées de suivi comme `errors` et `current_step`. Chaque agent reçoit cet état, y ajoute ses propres résultats, et retourne l'état complet mis à jour. Ce design garantit la traçabilité de la donnée tout au long du pipeline.

**La deuxième brique est la construction du graphe LangGraph.** Dans le fichier `graph.py`, j'ai manuellement déclaré chaque agent comme un nœud du graphe, puis j'ai défini les arêtes (transitions) entre eux pour former le pipeline séquentiel. LangGraph compile ce graphe en un objet exécutable qui expose une méthode `ainvoke()` asynchrone. C'est cette méthode qui est appelée depuis les routes FastAPI pour lancer l'ensemble du pipeline en une seule instruction. Le graphe est donc déterministe et reproductible : l'ordre d'exécution ne change jamais.

**La troisième brique est la différence fondamentale entre agents algorithmiques et agents LLM.** L'Agent 1 (Analysis Agent) est entièrement algorithmique : il n'appelle jamais le LLM. Il utilise Pandas pour charger et valider les CSV, puis invoque les trois analyzers (finance, marketing, support) et l'AnomalyDetector. Les KPIs sont calculés de façon mathématiquement exacte — la régression linéaire de Scikit-learn pour la tendance, la méthode IQR pour les anomalies. Cela garantit que l'IA ne peut jamais se tromper sur les chiffres, car elle ne les calcule pas : elle les reçoit déjà calculés.

**La quatrième brique est le prompt engineering dynamique.** Pour les agents qui utilisent le LLM (interprétation, recommandation, rapport), j'ai conçu des prompts système qui ancrent l'IA dans le contexte tunisien : monnaie en dinar (TND), TVA à 19%, référence aux organismes comme la BFPME. Le point clé est que les vraies valeurs numériques calculées par Pandas sont injectées directement dans le message utilisateur avant l'appel au LLM. Ainsi, le modèle DeepSeek-V3.2 reçoit des données concrètes et ne peut pas les inventer. Pour chaque agent LLM, la connexion à Azure AI Foundry est encapsulée dans une fonction `_get_llm()` séparée, ce qui la rend facilement remplaçable lors des tests.

**La cinquième brique est l'intelligence du RAG Agent.** Contrairement à une simple recherche textuelle, l'Agent 3 ne formule pas une requête générique. Il analyse d'abord les signaux présents dans l'état : si la marge bénéficiaire est inférieure à 10%, il formule une requête ciblée sur le redressement financier tunisien ; si le CA d'un canal est très faible, il cherche des guides sur l'optimisation commerciale ; si une catégorie de produit performe mal, il interroge les guides de gestion et logistique. Ces requêtes sont transformées en vecteurs de 768 dimensions par le modèle sentence-t5-base, puis comparées par similarité cosinus avec tous les chunks indexés dans ChromaDB. Les 3 passages les plus proches sémantiquement sont retournés avec leur source (nom du guide) et leur section (titre Markdown).

**La sixième brique est la validation par les tests.** Pour garantir que le pipeline fonctionne sans régression, j'ai écrit 85 tests répartis en quatre fichiers. Les tests des analyzers vérifient la précision des calculs sur des données connues. Les tests des agents utilisent la technique du mocking : la fonction `_get_llm()` est remplacée par un faux LLM qui retourne une réponse prédéfinie, ce qui permet de tester toute la logique de l'agent sans aucun appel réel à Azure AI Foundry. Les tests des routes vérifient que l'API renvoie les bons codes HTTP et la bonne structure JSON. Les tests du retriever vérifient la pertinence sémantique des résultats ChromaDB. Au total, les 85 tests passent en environ 35 secondes.

**La septième brique est le SQL Agent.** En complément du pipeline stratégique, j'ai ajouté un agent d'exploration de données. Un routeur d'intention (`intent_router`) analyse chaque question du chat et décide si elle relève de l'exploration de données ("Montre-moi le top 5...") ou de l'analyse stratégique ("Comment améliorer la marge..."). Dans le cas SQL, DeepSeek-V3.2 génère une requête SQL valide, un validateur de sécurité l'inspecte (SELECT only, pas de DROP/DELETE), puis DuckDB l'exécute en mémoire sur les 5 CSV chargés comme tables (ex. `ventes`, `regions`, `categories`, `canaux`, `kpis`). Le résultat est affiché dans la bulle de chat avec un tableau interactif, un graphique Recharts adapté (bar/line/pie/scatter), et un bouton d'export CSV.

En résumé : DeepSeek-V3.2 n'est que le moteur linguistique de surface. **L'intelligence métier, la logique d'analyse, l'orchestration du pipeline et le croisement avec les lois tunisiennes ont été entièrement développés sous forme de code algorithmique Python.**

---

## 4. L'Utilité et l'Importance de ce Projet

*   **Démocratisation du conseil :** Il offre aux petites entreprises tunisiennes un niveau d'analyse stratégique qui est normalement réservé aux grandes multinationales capables de payer des cabinets de conseil.
*   **Puissance et scalabilité :** En s'appuyant sur Azure AI Foundry et DeepSeek-V3.2, le système bénéficie d'une infrastructure cloud robuste et d'un modèle de langage à la pointe, sans contrainte matérielle locale.
*   **Prise de décision basée sur la donnée (Data-Driven) :** Le projet supprime l'intuition aléatoire. Les décisions sont prises sur la base de calculs mathématiques croisés avec une intelligence artificielle.

---

## 5. La Créativité et l'Innovation du Sujet

La véritable créativité scientifique de ce travail réside dans la **combinaison technologique** :
1.  **L'approche Multi-Agents :** C'est un sujet de recherche très actuel en IA (fin 2023 / 2024). Faire collaborer plusieurs agents permet de réduire drastiquement les "hallucinations" de l'IA (le fait qu'elle invente des choses), car chaque agent vérifie et complète le travail du précédent.
2.  **L'hybridation (Déterministe + Probabiliste) :** L'Agent 1 utilise des algorithmes mathématiques stricts (Scikit-learn, Pandas) pour être 100% exact sur les chiffres. C'est seulement ensuite que l'IA (probabiliste) intervient pour le texte. Cela garantit que l'IA ne se trompe jamais dans ses calculs financiers.
3.  **L'ancrage local (Le RAG Tunisien) :** Une IA générique ne connait pas la loi tunisienne. Mon système RAG injecte intelligemment la culture et la réglementation locale dans le "cerveau" de l'IA, la rendant experte du contexte tunisien.

---

## 6. Stack Technique Complète

### Tableau des technologies

| Couche | Technologie | Rôle |
|--------|-------------|------|
| **Frontend** | React 18 + Vite | Interface utilisateur SPA |
| **Frontend** | Tailwind CSS v3 | Styling utilitaire |
| **Frontend** | Recharts | Visualisation des KPIs |
| **Frontend** | Framer Motion | Animations fluides |
| **Frontend** | Axios + EventSource | HTTP + SSE streaming |
| **Frontend** | React Router v6 | Navigation entre pages |
| **Backend** | FastAPI 0.110+ | API REST + SSE asynchrone |
| **Backend** | Uvicorn | Serveur ASGI Python |
| **Backend** | Pydantic v2 | Validation des données |
| **Agents** | LangGraph 0.2+ | Orchestration du workflow multi-agents |
| **Agents** | LangChain 0.3+ | Abstraction LLM et RAG |
| **LLM** | DeepSeek-V3.2 | Modèle de langage (interprétation, recommandations) |
| **LLM** | Azure AI Foundry | Hébergement cloud du LLM |
| **Embeddings** | sentence-t5-base | Transformation texte → vecteurs 768d |
| **Vector DB** | ChromaDB 0.5+ | Stockage et recherche vectorielle locale |
| **Data Science** | Pandas + NumPy | Chargement, nettoyage, agrégation CSV |
| **Data Science** | Scikit-learn | Régression linéaire (tendances) |
| **SQL Agent** | DuckDB | Base analytique in-memory — 5 CSV comme tables SQL (ventes, regions, categories, canaux, kpis) |
| **SQL Agent** | intent_router | Classifie "sql" vs "strategic" par pattern matching |
| **Tests** | pytest 9 + pytest-asyncio | 105 tests unitaires et d'intégration |
| **Déploiement** | Docker + Docker Compose | Containerisation frontend + backend |

### Schéma du système RAG

```
  INGESTION (une seule fois)
  ─────────────────────────
  5 guides .md tunisiens
         │
         ▼
  MarkdownHeaderTextSplitter     ← découpe par section logique (#, ##, ###)
         │
         ▼
  RecursiveCharacterTextSplitter ← re-découpe si chunk > 500 chars
  (chunk_size=500, overlap=50)
         │
         ▼
  sentence-t5-base               ← encode chaque chunk → vecteur 768d
         │
         ▼
  ChromaDB (stockage local)      ← indexe vecteur + métadonnées
  backend/rag/chroma_db/

  RECHERCHE (à chaque requête)
  ────────────────────────────
  Requête sémantique (ex: "fiscalité TVA PME")
         │
         ▼
  sentence-t5-base               ← encode la requête → vecteur 768d
         │
         ▼
  Similarité cosinus              ← compare avec tous les vecteurs indexés
         │
         ▼
  Top-3 passages                  ← retourne les 3 chunks les plus proches
  + source (nom du guide)
  + section (titre Markdown)
```

### Structure des fichiers clés

```
backend/
├── agents/
│   ├── state.py                ← TypedDict : état partagé entre agents
│   ├── graph.py                ← Graphe LangGraph (5 noeuds séquentiels)
│   ├── analysis_agent.py       ← Calcul KPIs + détection anomalies IQR
│   ├── interpretation_agent.py ← Prompt dynamique → DeepSeek-V3.2
│   ├── rag_agent.py            ← Requêtes ChromaDB (sentence-t5-base)
│   ├── recommendation_agent.py ← Plan d'action priorisé via LLM
│   └── report_agent.py         ← Rapport JSON final structuré
├── analysis/
│   ├── loader.py               ← Validation et nettoyage des CSV
│   ├── finance_analyzer.py     ← KPIs financiers (revenue, profit, marge, panier moyen)
│   ├── marketing_analyzer.py   ← KPIs canaux (CA par canal, meilleur canal, transactions)
│   ├── support_analyzer.py     ← KPIs catégories (CA/profit par catégorie, top catégorie)
│   └── anomaly_detector.py     ← Méthode IQR (Q1-1.5·IQR / Q3+1.5·IQR)
├── rag/
│   ├── embeddings.py           ← sentence-t5-base (normalize=True, dim=768)
│   ├── ingest.py               ← Chunking hybride + indexation ChromaDB
│   └── retriever.py            ← Similarité cosinus, top-k configurable
├── routes/
│   ├── analyze.py              ← POST /analyze → lance run_graph_async()
│   ├── upload.py               ← POST /upload  → valide et stocke CSV
│   ├── chat.py                 ← POST /chat    → SSE + intent routing (sql/strategic)
│   ├── report.py               ← GET /report   → lit last_report.json
│   └── sql.py                  ← POST /sql/query → NL→SQL→DuckDB→JSON
├── sql_agent/
│   ├── db.py                   ← DuckDB in-memory : charge les 5 CSV comme tables (ventes, regions, categories, canaux, kpis)
│   ├── validator.py            ← Sécurité : SELECT only, mots-clés interdits
│   ├── generator.py            ← DeepSeek → SQL + viz_type (bar/line/pie/scatter/table)
│   ├── executor.py             ← Exécution async, timeout 10s, max 500 lignes
│   └── intent_router.py        ← Classifie "sql" ou "strategic" par regex scoring
└── tests/
    ├── test_analysis.py        ← 38 tests : analyzers + anomaly detector
    ├── test_agents.py          ← 16 tests : state, analysis_agent, pipeline
    ├── test_rag.py             ← 15 tests : structure, pertinence, robustesse
    ├── test_routes.py          ← 16 tests : /health, /upload, /analyze, /report
    └── test_sql_agent.py       ← 20 tests : validate_sql, enforce_limit,
                                              classify_intent, execute_sql, POST /sql/query
                                   ─────────────────────────
                                   TOTAL : 105/105 tests passés
```

---

## 7. Les Données Utilisées

Les jeux de données principaux sont stockés dans `data/uploads/` et comprennent 5 fichiers :

| Fichier | Colonnes principales (ex.) | KPIs calculés |
|--------:|---------------------------|---------------|
| `01_donnees_vente.csv` | date, product_id, product_name, region, channel, revenue, quantity | CA par produit, top produits, panier moyen |
| `02_analyse_region.csv` | date, region, revenue, orders, avg_ticket | CA par région, part de marché régionale, tendance régionale |
| `03_analyse_categorie.csv` | date, category, revenue, conversions | CA par catégorie, top catégories, conversion par catégorie |
| `04_analyse_canaux.csv` | date, channel, budget, clicks, conversions, revenue | ROI par canal, taux conversion par canal, coût/conversion |
| `05_kpis_globaux.csv` | period, total_revenue, total_cost, total_profit, overall_growth_rate | KPIs agrégés (revenue_total, profit_margin, avg_growth_rate, volatility) |

**Contexte tunisien pris en compte dans les prompts :**
- Monnaie : Dinar Tunisien (TND)
- Fiscalité : TVA 19%, IS 15% PME
- Organismes : BFPME, SOTUGAR
- Saisonnalité : Ramadan dans l'analyse marketing
- Références légales : loi 2016-71 sur l'investissement, Code du travail tunisien
