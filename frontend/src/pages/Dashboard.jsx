/**
 * Dashboard — page d'accueil avec les KPIs principaux.
 */

import { useEffect } from 'react';
import { motion } from 'framer-motion';
import { Link } from 'react-router-dom';
import KpiCard from '../components/KpiCard';
import { ChannelChart } from '../components/Charts';
import useAnalysis from '../hooks/useAnalysis';

/**
 * Page Dashboard.
 */
const Dashboard = () => {
  const { kpis, report, isLoading, error, fetchReport, triggerAnalysis } = useAnalysis();

  useEffect(() => {
    fetchReport();
  }, [fetchReport]);

  const financeKpis = kpis.finance?.indicateurs || [];
  const marketingKpis = kpis.marketing?.indicateurs || [];
  const categoriesKpis = kpis.categories?.indicateurs || [];

  return (
    <div className="min-h-[calc(100vh-4rem)] p-6">
      <motion.div
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.35 }}
        className="mb-8"
      >
        <h1 className="text-3xl font-bold text-white drop-shadow-sm">
          Tableau de Bord
        </h1>
        <p className="mt-2 text-cyan-200/90">
          Vue d&apos;ensemble des performances de votre entreprise
        </p>
      </motion.div>

      <motion.div
        className="mb-8 flex flex-wrap gap-4"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.1 }}
      >
        <motion.button
          type="button"
          onClick={() => triggerAnalysis(true)}
          disabled={isLoading}
          className="px-6 py-3 rounded-xl font-medium text-cyan-950 bg-gradient-to-r from-cyan-300 to-teal-300 shadow-lg shadow-cyan-900/30 disabled:opacity-50 disabled:cursor-not-allowed"
          whileHover={{ scale: isLoading ? 1 : 1.03 }}
          whileTap={{ scale: isLoading ? 1 : 0.98 }}
        >
          {isLoading ? 'Analyse en cours...' : 'Lancer l\'analyse'}
        </motion.button>
        <motion.div whileHover={{ scale: 1.03 }} whileTap={{ scale: 0.98 }}>
          <Link
            to="/chat"
            className="inline-block px-6 py-3 rounded-xl font-medium text-white border-2 border-cyan-400/50 bg-cyan-500/20 backdrop-blur-sm hover:bg-cyan-500/35 transition-colors"
          >
            Poser une question
          </Link>
        </motion.div>
      </motion.div>

      {error && (
        <motion.div
          initial={{ opacity: 0, x: -8 }}
          animate={{ opacity: 1, x: 0 }}
          className="mb-8 p-4 rounded-xl bg-rose-500/20 border border-rose-400/40 text-rose-100"
        >
          {error}
        </motion.div>
      )}

      {!isLoading && Object.keys(kpis).length === 0 && (
        <motion.div
          initial={{ opacity: 0, scale: 0.98 }}
          animate={{ opacity: 1, scale: 1 }}
          className="mb-8 p-8 glass-panel text-center"
        >
          <svg className="w-16 h-16 mx-auto text-cyan-300/80 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
          </svg>
          <h2 className="text-xl font-semibold text-white mb-2">
            Aucune analyse disponible
          </h2>
          <p className="text-cyan-200/90 mb-4">
            Lancez une analyse pour voir les KPIs de votre entreprise.
          </p>
        </motion.div>
      )}

      {Object.keys(kpis).length > 0 && (
        <>
          <section className="mb-8">
            <h2 className="text-xl font-semibold text-cyan-100 mb-4 flex items-center gap-2">
              <span>📊</span> Performance Financière
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              {financeKpis.map((kpi, index) => (
                <motion.div
                  key={kpi.label}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: index * 0.08 }}
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

          <section className="mb-8">
            <h2 className="text-xl font-semibold text-cyan-100 mb-4 flex items-center gap-2">
              <span>📈</span> Performance Marketing
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              {marketingKpis.map((kpi, index) => (
                <motion.div
                  key={kpi.label}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: index * 0.08 }}
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

            {kpis.marketing?.ca_par_canal && (
              <motion.div
                initial={{ opacity: 0, y: 12 }}
                animate={{ opacity: 1, y: 0 }}
                className="mt-6 glass-panel p-6"
              >
                <h3 className="text-lg font-medium text-white mb-4">CA par Canal</h3>
                <ChannelChart data={kpis.marketing.ca_par_canal} />
              </motion.div>
            )}
          </section>

          <section className="mb-8">
            <h2 className="text-xl font-semibold text-cyan-100 mb-4 flex items-center gap-2">
              <span>📦</span> Performance par Catégorie
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              {categoriesKpis.map((kpi, index) => (
                <motion.div
                  key={kpi.label}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: index * 0.08 }}
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
          </section>

          {report?.resume_executif && (
            <section className="mb-8">
              <h2 className="text-xl font-semibold text-cyan-100 mb-4 flex items-center gap-2">
                <span>📋</span> Résumé Exécutif
              </h2>
              <div className="glass-panel p-6">
                <p className="text-cyan-100/95 leading-relaxed">
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
