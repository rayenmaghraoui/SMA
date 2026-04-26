# ============================================================
# Frontend Dockerfile — AI Business Consultant
# Build multi-étapes : build (Node) → serve (Nginx)
# ============================================================

# ============================================================
# ÉTAPE 1 : Build — Node 18 Alpine (image légère)
# ============================================================

FROM node:18-alpine AS builder

LABEL stage="builder"

WORKDIR /app

# Optimisation du cache Docker — copier package.json avant le code source
# pour ne reconstruire cette couche que si les dépendances changent
COPY package.json package-lock.json ./

RUN npm ci --frozen-lockfile

# Copier tout le code source du frontend
COPY . .

# Passer la variable d'environnement de l'API backend pour le build Vite
# Le frontend utilisera /api comme préfixe (proxy Nginx vers le backend)
ARG VITE_API_URL=/api
ENV VITE_API_URL=${VITE_API_URL}

# Compiler l'application React pour la production
RUN npm run build

# ============================================================
# ÉTAPE 2 : Serve — Nginx Alpine (image minimale)
# ============================================================

FROM nginx:alpine AS production

LABEL maintainer="AI Business Consultant PFE"
LABEL description="Frontend React 18 + Vite + Tailwind CSS"

# Copier les fichiers buildés depuis l'étape précédente
COPY --from=builder /app/dist /usr/share/nginx/html

# Copier la configuration Nginx personnalisée
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Créer les répertoires de logs Nginx
RUN mkdir -p /var/log/nginx

EXPOSE 80

# Healthcheck Nginx
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD wget -q --spider http://localhost:80 || exit 1

CMD ["nginx", "-g", "daemon off;"]
