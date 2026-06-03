/**
 * Hook useAnalysis — gestion de l'analyse des données.
 */

import { useState, useCallback } from 'react';
import api from '../services/api';
import { toast } from '../services/toast';

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
  // true après la tentative initiale de chargement du rapport
  const [initialLoadDone, setInitialLoadDone] = useState(false);

  /**
   * Lance l'analyse complète des données.
   * @param {boolean} useDefaults - Utiliser les données par défaut
   */
  const triggerAnalysis = useCallback(async (useDefaults = true, force = false) => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await api.post('/analyze', { use_defaults: useDefaults, force });
      const data = response.data;

      if (data.success) {
        setAnomalies(data.anomalies || []);

        // Le rapport sauvegardé contient les kpis au format "indicateurs"
        // attendu par le Dashboard (kpis.finance.indicateurs, etc.).
        // Le /analyze retourne le format brut du pipeline — on recharge
        // le rapport pour avoir la structure correcte.
        try {
          const reportResp = await api.get('/report/latest');
          const rd = reportResp.data;
          if (rd?.success && rd?.has_report) {
            setReport(rd.report);
            setKpis(rd.report?.kpis || {});
          } else {
            setKpis(data.kpis || {});
          }
        } catch {
          setKpis(data.kpis || {});
        }
        toast.success('Analyse terminée — rapport disponible.');
      } else {
        const errMsg = data.errors?.join(', ') || 'Erreur inconnue';
        setError(errMsg);
        toast.error(`Analyse échouée : ${errMsg}`);
      }
    } catch (err) {
      const message = err.response?.data?.detail || err.message || 'Erreur serveur';
      setError(message);
      toast.error(message);
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
      setInitialLoadDone(true);   // signale que la tentative initiale est terminée
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
    initialLoadDone,
    triggerAnalysis,
    fetchReport,
    fetchKpis,
    reset,
  };
};

export default useAnalysis;
