/**
 * Dashboard — page d'accueil avec les KPIs principaux.
 */

import { useEffect } from 'react';
import { motion } from 'framer-motion';
import { Link } from 'react-router-dom';
import KpiCard from '../components/KpiCard';
import { RevenueChart, ChannelChart } from '../components/Charts';
import useAnalysis from '../hooks/useAnalysis';

/**
 * Page Dashboard.
 */
const Dashboard = () => {
  const { kpis, report, isLoading, error, fetchReport, triggerAnalysis } = useAnalysis();

  // Charger le rapport au montage
  useEffect(() => {
    fetchReport();
  }, [fetchReport]);

  // Extraire les KPIs par domaine
  const financeKpis = kpis.finance?.indicateurs || [];
  const marketingKpis = kpis.marketing?.indicateurs || [];
  const supportKpis = kpis.support?.indicateurs || [];

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">
          Tableau de Bord
        </h1>
        <p className="mt-2 text-gray-600">
          Vue d'ensemble des performances de votre entreprise
        </p>
      </div>

      {/* Actions */}
      <div className="mb-8 flex gap-4">
        <button
          onClick={() => triggerAnalysis(true)}
          disabled={isLoading}
          className="px-6 py-3 bg-blue-500 text-white rounded-lg font-medium hover:bg-blue-600 transition-colors disabled:opacity-50"
        >
          {isLoading ? 'Analyse en cours...' : 'Lancer l\'analyse'}
        </button>
        <Link
          to="/chat"
          className="px-6 py-3 bg-purple-500 text-white rounded-lg font-medium hover:bg-purple-600 transition-colors"
        >
          Poser une question
        </Link>
      </div>

      {/* Erreur */}
      {error && (
        <div className="mb-8 p-4 bg-red-100 text-red-700 rounded-lg">
          {error}
        </div>
      )}

      {/* Message si pas de données */}
      {!isLoading && Object.keys(kpis).length === 0 && (
        <div className="mb-8 p-8 bg-white rounded-xl shadow-md text-center">
          <svg className="w-16 h-16 mx-auto text-gray-400 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
          </svg>
          <h2 className="text-xl font-semibold text-gray-900 mb-2">
            Aucune analyse disponible
          </h2>
          <p className="text-gray-600 mb-4">
            Lancez une analyse pour voir les KPIs de votre entreprise.
          </p>
        </div>
      )}

      {/* Grille de KPIs */}
      {Object.keys(kpis).length > 0 && (
        <>
          {/* Section Finance */}
          <section className="mb-8">
            <h2 className="text-xl font-semibold text-gray-900 mb-4 flex items-center gap-2">
              <span>📊</span> Performance Financière
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              {financeKpis.map((kpi, index) => (
                <motion.div
                  key={kpi.label}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: index * 0.1 }}
                >
                  <KpiCard
                    label={kpi.label}
                    value={kpi.valeur}
                    format={kpi.format}
                    unite={kpi.unite}
                    trend={kpi.label.includes('Tendance') ? kpi.valeur : null}
                  />
                </motion.div>
              ))}
            </div>
          </section>

          {/* Section Marketing */}
          <section className="mb-8">
            <h2 className="text-xl font-semibold text-gray-900 mb-4 flex items-center gap-2">
              <span>📈</span> Performance Marketing
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              {marketingKpis.map((kpi, index) => (
                <motion.div
                  key={kpi.label}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: index * 0.1 }}
                >
                  <KpiCard
                    label={kpi.label}
                    value={kpi.valeur}
                    format={kpi.format}
                    unite={kpi.unite}
                  />
                </motion.div>
              ))}
            </div>

            {/* Graphique ROI par canal */}
            {kpis.marketing?.roi_par_canal && (
              <div className="mt-6 bg-white rounded-xl shadow-md p-6">
                <h3 className="text-lg font-medium text-gray-900 mb-4">ROI par Canal</h3>
                <ChannelChart data={kpis.marketing.roi_par_canal} />
              </div>
            )}
          </section>

          {/* Section Support */}
          <section className="mb-8">
            <h2 className="text-xl font-semibold text-gray-900 mb-4 flex items-center gap-2">
              <span>🎧</span> Service Client
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              {supportKpis.map((kpi, index) => (
                <motion.div
                  key={kpi.label}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: index * 0.1 }}
                >
                  <KpiCard
                    label={kpi.label}
                    value={kpi.valeur}
                    format={kpi.format}
                    unite={kpi.unite}
                    inverseTrend={kpi.label.includes('churn') || kpi.label.includes('résolution')}
                  />
                </motion.div>
              ))}
            </div>
          </section>

          {/* Résumé exécutif */}
          {report?.resume_executif && (
            <section className="mb-8">
              <h2 className="text-xl font-semibold text-gray-900 mb-4 flex items-center gap-2">
                <span>📋</span> Résumé Exécutif
              </h2>
              <div className="bg-white rounded-xl shadow-md p-6">
                <p className="text-gray-700 leading-relaxed">
                  {report.resume_executif}
                </p>
              </div>
            </section>
          )}
        </>
      )}
    </div>
  );
};

export default Dashboard;
