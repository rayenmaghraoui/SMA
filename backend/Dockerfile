# ============================================================
# Backend Dockerfile — AI Business Consultant
# Image de base légère Python 3.10
# ============================================================

FROM python:3.10-slim

# Métadonnées
LABEL maintainer="AI Business Consultant PFE"
LABEL description="Backend FastAPI — Multi-agents LangGraph + RAG ChromaDB"

# ============================================================
# Variables d'environnement système
# ============================================================

# Empêche Python de créer des .pyc et des buffers stdout
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Répertoire de travail à la racine du projet (important pour les imports backend.*)
WORKDIR /app

# ============================================================
# Dépendances système (nécessaires pour certains packages Python)
# ============================================================

RUN apt-get update && apt-get install -y --no-install-recommends \
    # Nécessaire pour la compilation de certains packages C/C++
    build-essential \
    # Pour les healthchecks HTTP (curl)
    curl \
    # Pour sentence-transformers (téléchargement des modèles)
    git \
    && rm -rf /var/lib/apt/lists/*

# ============================================================
# Optimisation du cache Docker — installer les dépendances AVANT
# de copier le code source (la couche est reconstruite uniquement
# si requirements.txt change)
# ============================================================

COPY requirements.txt .

RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# ============================================================
# Copie du code source
# ============================================================

# Copier le backend (module Python principal)
COPY backend/ ./backend/

# Copier les données et documents nécessaires au RAG
COPY data/ ./data/
COPY documents/ ./documents/

# ============================================================
# Création des répertoires nécessaires
# ============================================================

RUN mkdir -p ./data/uploads \
    && mkdir -p ./backend/rag/chroma_db

# ============================================================
# Sécurité — utiliser un utilisateur non-root
# ============================================================

RUN useradd --create-home --shell /bin/bash appuser && \
    chown -R appuser:appuser /app
USER appuser

# ============================================================
# Exposition du port et commande de démarrage
# ============================================================

EXPOSE 8000

# Healthcheck — vérifie que l'API répond avant de considérer
# le conteneur comme prêt
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Démarrer l'application via le module Python (respecte les imports backend.*)
CMD ["python", "-m", "uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
