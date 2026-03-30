/**
 * Hook useAnalysis — gestion de l'analyse des données.
 */

import { useState, useCallback } from 'react';
import api from '../services/api';

/**
 * Hook pour gérer l'analyse des données.
 *
 * @returns {{
 *   kpis: Object,
 *   anomalies: Array,
 *   report: Object|null,
 *   isLoading: boolean,
 *   error: string|null,
 *   triggerAnalysis: function,
 *   fetchReport: function,
 *   reset: function
 * }}
 */
export const useAnalysis = () => {
  const [kpis, setKpis] = useState({});
  const [anomalies, setAnomalies] = useState([]);
  const [report, setReport] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  /**
   * Lance l'analyse complète des données.
   * @param {boolean} useDefaults - Utiliser les données par défaut
   */
  const triggerAnalysis = useCallback(async (useDefaults = true) => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await api.post('/analyze', { use_defaults: useDefaults });
      const data = response.data;

      if (data.success) {
        setKpis(data.kpis || {});
        setAnomalies(data.anomalies || []);
        setReport(data.report || null);
      } else {
        setError(data.errors?.join(', ') || 'Erreur inconnue');
      }
    } catch (err) {
      const message = err.response?.data?.detail || err.message || 'Erreur serveur';
      setError(message);
      console.error('Erreur analyse:', err);
    } finally {
      setIsLoading(false);
    }
  }, []);

  /**
   * Récupère le dernier rapport généré.
   */
  const fetchReport = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await api.get('/report/latest');
      const data = response.data;

      if (data.success && data.has_report) {
        setReport(data.report);
        setKpis(data.report?.kpis || {});
      } else {
        setReport(null);
        setKpis({});
      }
    } catch (err) {
      const message = err.response?.data?.detail || err.message;
      setError(message);
    } finally {
      setIsLoading(false);
    }
  }, []);

  /**
   * Récupère uniquement les KPIs du rapport.
   */
  const fetchKpis = useCallback(async () => {
    try {
      const response = await api.get('/report/kpis');
      if (response.data.success) {
        setKpis(response.data.kpis);
      }
    } catch (err) {
      console.error('Erreur fetch KPIs:', err);
    }
  }, []);

  /**
   * Réinitialise l'état.
   */
  const reset = useCallback(() => {
    setKpis({});
    setAnomalies([]);
    setReport(null);
    setError(null);
  }, []);

  return {
    kpis,
    anomalies,
    report,
    isLoading,
    error,
    triggerAnalysis,
    fetchReport,
    fetchKpis,
    reset,
  };
};

export default useAnalysis;
