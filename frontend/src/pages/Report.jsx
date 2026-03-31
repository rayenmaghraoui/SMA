/**
 * Report — affichage du rapport complet.
 */

import { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import api from '../services/api';

/**
 * Carte de recommandation.
 */
const RecommendationCard = ({ recommendation, index }) => {
  const priorityColors = {
    1: 'bg-rose-500',
    2: 'bg-orange-500',
    3: 'bg-amber-400',
    4: 'bg-cyan-500',
    5: 'bg-slate-500',
  };

  return (
    <motion.div
      initial={{ opacity: 0, x: -20 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ delay: index * 0.08 }}
      className="glass-panel p-6"
    >
      <div className="flex items-start gap-4">
        <div className={`w-8 h-8 ${priorityColors[recommendation.priorite] || priorityColors[5]} rounded-full flex items-center justify-center text-white font-bold text-sm shadow-lg`}>
          {recommendation.priorite}
        </div>
        <div className="flex-1">
          <h3 className="text-lg font-semibold text-white">
            {recommendation.titre}
          </h3>
          <p className="mt-2 text-cyan-100/90">
            {recommendation.action}
          </p>
          <div className="mt-4 flex flex-wrap gap-2">
            <span className="px-3 py-1 rounded-full text-sm text-emerald-100 bg-emerald-500/25 border border-emerald-400/35">
              Impact: {recommendation.impact}
            </span>
            {recommendation.source && (
              <span className="px-3 py-1 rounded-full text-sm text-cyan-100 bg-cyan-500/25 border border-cyan-400/35">
                {recommendation.source}
              </span>
            )}
          </div>
        </div>
      </div>
    </motion.div>
  );
};

/**
 * Page Report.
 */
const Report = () => {
  const [report, setReport] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchReport = async () => {
      try {
        const response = await api.get('/report');
        setReport(response.data.report);
      } catch (err) {
        if (err.response?.status === 404) {
          setError("Aucun rapport disponible. Lancez d'abord une analyse.");
        } else {
          setError(err.response?.data?.detail || 'Erreur lors du chargement');
        }
      } finally {
        setIsLoading(false);
      }
    };

    fetchReport();
  }, []);

  if (isLoading) {
    return (
      <div className="min-h-[calc(100vh-4rem)] flex items-center justify-center">
        <motion.div
          className="w-12 h-12 rounded-full border-4 border-cyan-400/30 border-t-cyan-300"
          animate={{ rotate: 360 }}
          transition={{ duration: 0.9, repeat: Infinity, ease: 'linear' }}
        />
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-[calc(100vh-4rem)] flex items-center justify-center p-6">
        <motion.div
          initial={{ opacity: 0, scale: 0.98 }}
          animate={{ opacity: 1, scale: 1 }}
          className="text-center glass-panel p-8 max-w-md"
        >
          <svg className="w-16 h-16 mx-auto text-cyan-300/70 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
          <p className="text-cyan-100">{error}</p>
        </motion.div>
      </div>
    );
  }

  return (
    <div className="min-h-[calc(100vh-4rem)] p-6">
      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        className="mb-8 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4"
      >
        <div>
          <h1 className="text-3xl font-bold text-white">
            Rapport d&apos;Analyse
          </h1>
          <p className="mt-2 text-cyan-200/90">
            Généré le {new Date(report?.metadata?.date_generation).toLocaleString('fr-FR')}
          </p>
        </div>
        <motion.button
          type="button"
          onClick={() => window.print()}
          className="px-4 py-2 rounded-xl text-cyan-950 bg-cyan-200/90 hover:bg-cyan-100 transition-colors flex items-center justify-center gap-2 w-fit"
          whileHover={{ scale: 1.03 }}
          whileTap={{ scale: 0.98 }}
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 17h2a2 2 0 002-2v-4a2 2 0 00-2-2H5a2 2 0 00-2 2v4a2 2 0 002 2h2m2 4h6a2 2 0 002-2v-4a2 2 0 00-2-2H9a2 2 0 00-2 2v4a2 2 0 002 2zm8-12V5a2 2 0 00-2-2H9a2 2 0 00-2 2v4h10z" />
          </svg>
          Imprimer
        </motion.button>
      </motion.div>

      <section className="mb-8">
        <h2 className="text-xl font-semibold text-cyan-100 mb-4 flex items-center gap-2">
          <span>📋</span> Résumé Exécutif
        </h2>
        <div className="glass-panel p-6">
          <p className="text-cyan-100/95 leading-relaxed text-lg">
            {report?.resume_executif}
          </p>
        </div>
      </section>

      {report?.interpretation && (
        <section className="mb-8">
          <h2 className="text-xl font-semibold text-cyan-100 mb-4 flex items-center gap-2">
            <span>🧠</span> Analyse Détaillée
          </h2>
          <div className="glass-panel p-6">
            <div className="max-w-none">
              {report.interpretation.split('\n').map((paragraph, i) => (
                <p key={i} className="mb-4 text-cyan-100/90 leading-relaxed">
                  {paragraph}
                </p>
              ))}
            </div>
          </div>
        </section>
      )}

      <section className="mb-8">
        <h2 className="text-xl font-semibold text-cyan-100 mb-4 flex items-center gap-2">
          <span>💡</span> Recommandations Stratégiques
        </h2>
        <div className="space-y-4">
          {report?.recommendations?.map((rec, index) => (
            <RecommendationCard key={index} recommendation={rec} index={index} />
          ))}
        </div>
      </section>

      {report?.anomalies?.total > 0 && (
        <section className="mb-8">
          <h2 className="text-xl font-semibold text-cyan-100 mb-4 flex items-center gap-2">
            <span>⚠️</span> Anomalies Détectées ({report.anomalies.total})
          </h2>
          <div className="glass-panel p-6 overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-cyan-400/25">
                  <th className="text-left py-3 px-4 text-cyan-300/90">Dataset</th>
                  <th className="text-left py-3 px-4 text-cyan-300/90">Colonne</th>
                  <th className="text-left py-3 px-4 text-cyan-300/90">Valeur</th>
                  <th className="text-left py-3 px-4 text-cyan-300/90">Type</th>
                </tr>
              </thead>
              <tbody>
                {report.anomalies.details.slice(0, 10).map((anomaly, i) => (
                  <tr key={i} className="border-b border-cyan-500/15 last:border-0">
                    <td className="py-3 px-4 capitalize text-cyan-100">{anomaly.dataset}</td>
                    <td className="py-3 px-4 text-cyan-100">{anomaly.colonne}</td>
                    <td className="py-3 px-4 font-mono text-cyan-200">{anomaly.valeur}</td>
                    <td className="py-3 px-4">
                      <span className={`px-2 py-1 rounded text-sm ${anomaly.type === 'high' ? 'bg-rose-500/25 text-rose-200 border border-rose-400/35' : 'bg-cyan-500/25 text-cyan-100 border border-cyan-400/35'}`}>
                        {anomaly.type === 'high' ? '↑ Élevée' : '↓ Basse'}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      )}

      {report?.sources_rag?.length > 0 && (
        <section className="mb-8">
          <h2 className="text-xl font-semibold text-cyan-100 mb-4 flex items-center gap-2">
            <span>📚</span> Sources Consultées
          </h2>
          <div className="glass-panel p-6">
            <div className="space-y-2">
              {report.sources_rag.map((source, i) => (
                <div key={i} className="flex items-center gap-2 text-cyan-100/90">
                  <svg className="w-4 h-4 text-cyan-400 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                  <span>{source.document}</span>
                  {source.section && (
                    <span className="text-cyan-400/70">— {source.section}</span>
                  )}
                </div>
              ))}
            </div>
          </div>
        </section>
      )}
    </div>
  );
};

export default Report;
