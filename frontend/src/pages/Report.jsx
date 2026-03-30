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
    1: 'bg-red-500',
    2: 'bg-orange-500',
    3: 'bg-yellow-500',
    4: 'bg-blue-500',
    5: 'bg-gray-500',
  };

  return (
    <motion.div
      initial={{ opacity: 0, x: -20 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ delay: index * 0.1 }}
      className="bg-white rounded-xl shadow-md p-6"
    >
      <div className="flex items-start gap-4">
        <div className={`w-8 h-8 ${priorityColors[recommendation.priorite] || priorityColors[5]} rounded-full flex items-center justify-center text-white font-bold text-sm`}>
          {recommendation.priorite}
        </div>
        <div className="flex-1">
          <h3 className="text-lg font-semibold text-gray-900">
            {recommendation.titre}
          </h3>
          <p className="mt-2 text-gray-600">
            {recommendation.action}
          </p>
          <div className="mt-4 flex flex-wrap gap-2">
            <span className="px-3 py-1 bg-green-100 text-green-700 rounded-full text-sm">
              Impact: {recommendation.impact}
            </span>
            {recommendation.source && (
              <span className="px-3 py-1 bg-blue-100 text-blue-700 rounded-full text-sm">
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

  // Charger le rapport
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
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="animate-spin w-12 h-12 border-4 border-blue-500 border-t-transparent rounded-full" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <svg className="w-16 h-16 mx-auto text-gray-400 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
          <p className="text-gray-600">{error}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">
              Rapport d'Analyse
            </h1>
            <p className="mt-2 text-gray-600">
              Généré le {new Date(report?.metadata?.date_generation).toLocaleString('fr-FR')}
            </p>
          </div>
          <button
            onClick={() => window.print()}
            className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors flex items-center gap-2"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 17h2a2 2 0 002-2v-4a2 2 0 00-2-2H5a2 2 0 00-2 2v4a2 2 0 002 2h2m2 4h6a2 2 0 002-2v-4a2 2 0 00-2-2H9a2 2 0 00-2 2v4a2 2 0 002 2zm8-12V5a2 2 0 00-2-2H9a2 2 0 00-2 2v4h10z" />
            </svg>
            Imprimer
          </button>
        </div>
      </div>

      {/* Résumé exécutif */}
      <section className="mb-8">
        <h2 className="text-xl font-semibold text-gray-900 mb-4 flex items-center gap-2">
          <span>📋</span> Résumé Exécutif
        </h2>
        <div className="bg-white rounded-xl shadow-md p-6">
          <p className="text-gray-700 leading-relaxed text-lg">
            {report?.resume_executif}
          </p>
        </div>
      </section>

      {/* Interprétation */}
      {report?.interpretation && (
        <section className="mb-8">
          <h2 className="text-xl font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <span>🧠</span> Analyse Détaillée
          </h2>
          <div className="bg-white rounded-xl shadow-md p-6">
            <div className="prose max-w-none">
              {report.interpretation.split('\n').map((paragraph, i) => (
                <p key={i} className="mb-4 text-gray-700 leading-relaxed">
                  {paragraph}
                </p>
              ))}
            </div>
          </div>
        </section>
      )}

      {/* Recommandations */}
      <section className="mb-8">
        <h2 className="text-xl font-semibold text-gray-900 mb-4 flex items-center gap-2">
          <span>💡</span> Recommandations Stratégiques
        </h2>
        <div className="space-y-4">
          {report?.recommendations?.map((rec, index) => (
            <RecommendationCard key={index} recommendation={rec} index={index} />
          ))}
        </div>
      </section>

      {/* Anomalies */}
      {report?.anomalies?.total > 0 && (
        <section className="mb-8">
          <h2 className="text-xl font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <span>⚠️</span> Anomalies Détectées ({report.anomalies.total})
          </h2>
          <div className="bg-white rounded-xl shadow-md p-6">
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b">
                    <th className="text-left py-3 px-4 text-gray-600">Dataset</th>
                    <th className="text-left py-3 px-4 text-gray-600">Colonne</th>
                    <th className="text-left py-3 px-4 text-gray-600">Valeur</th>
                    <th className="text-left py-3 px-4 text-gray-600">Type</th>
                  </tr>
                </thead>
                <tbody>
                  {report.anomalies.details.slice(0, 10).map((anomaly, i) => (
                    <tr key={i} className="border-b last:border-0">
                      <td className="py-3 px-4 capitalize">{anomaly.dataset}</td>
                      <td className="py-3 px-4">{anomaly.colonne}</td>
                      <td className="py-3 px-4 font-mono">{anomaly.valeur}</td>
                      <td className="py-3 px-4">
                        <span className={`px-2 py-1 rounded text-sm ${anomaly.type === 'high' ? 'bg-red-100 text-red-700' : 'bg-blue-100 text-blue-700'}`}>
                          {anomaly.type === 'high' ? '↑ Élevée' : '↓ Basse'}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </section>
      )}

      {/* Sources */}
      {report?.sources_rag?.length > 0 && (
        <section className="mb-8">
          <h2 className="text-xl font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <span>📚</span> Sources Consultées
          </h2>
          <div className="bg-white rounded-xl shadow-md p-6">
            <div className="space-y-2">
              {report.sources_rag.map((source, i) => (
                <div key={i} className="flex items-center gap-2 text-gray-600">
                  <svg className="w-4 h-4 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                  <span>{source.document}</span>
                  {source.section && (
                    <span className="text-gray-400">— {source.section}</span>
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
