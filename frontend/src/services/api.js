/**
 * Configuration Axios — instance API centrale.
 *
 * Cette instance est pré-configurée avec :
 * - baseURL depuis les variables d'environnement
 * - Intercepteurs pour la gestion des erreurs
 * - Headers par défaut
 */

import axios from 'axios';

// URL de base de l'API
const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// Instance Axios configurée
const api = axios.create({
  baseURL: API_URL,
  timeout: 300000, // 5 minutes (le pipeline 5 agents + LLM peut prendre du temps)
  headers: {
    'Content-Type': 'application/json',
  },
});

// Intercepteur de requête
api.interceptors.request.use(
  (config) => {
    // Log en développement
    if (import.meta.env.DEV) {
      console.log(`[API] ${config.method?.toUpperCase()} ${config.url}`);
    }
    return config;
  },
  (error) => {
    console.error('[API] Erreur requête:', error);
    return Promise.reject(error);
  }
);

// Intercepteur de réponse
api.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    // Gestion des erreurs HTTP
    if (error.response) {
      const { status, data } = error.response;
      const requestUrl = error.config?.url || '';
      const isExpectedMissingReport = status === 404 && requestUrl.startsWith('/report');

      // Aucun rapport au démarrage est un cas normal.
      if (isExpectedMissingReport) {
        return Promise.reject(error);
      }

      switch (status) {
        case 400:
          console.error('[API] Requête invalide:', data.detail || data);
          break;
        case 404:
          console.error('[API] Ressource non trouvée:', data.detail || data);
          break;
        case 500:
          console.error('[API] Erreur serveur:', data.detail || data);
          break;
        default:
          console.error(`[API] Erreur ${status}:`, data);
      }
    } else if (error.request) {
      console.error('[API] Pas de réponse du serveur');
    } else {
      console.error('[API] Erreur:', error.message);
    }

    return Promise.reject(error);
  }
);

/**
 * Vérifie l'état de santé de l'API.
 * @returns {Promise<{status: string, api: boolean, ollama: boolean}>}
 */
export const checkHealth = async () => {
  const response = await api.get('/health');
  return response.data;
};

/**
 * Récupère les informations du pipeline.
 * @returns {Promise<Object>}
 */
export const getPipelineInfo = async () => {
  const response = await api.get('/pipeline');
  return response.data;
};

export default api;
