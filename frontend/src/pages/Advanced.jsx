/**
 * Advanced — page « Analyse avancée ».
 *
 * Regroupe deux analyses orientées aide à la décision :
 *   1. Prévision des ventes (forecasting saisonnier).
 *   2. Comparaison de deux périodes.
 */

import { useEffect, useState, useCallback } from 'react';
import { motion } from 'framer-motion';
import { ForecastChart, CategoryComparisonChart } from '../components/AdvancedCharts';
import { getDateRange, fetchForecast, comparePeriods } from '../services/advancedService';

/** Formate un nombre en TND. */
const fmtTND = (v) => `${Math.round(v).toLocaleString('fr-FR')} TND`;

/** Badge d'évolution coloré (vert si positif, rouge si négatif). */
const EvolutionBadge = ({ value, suffix = '%' }) => {
  const positive = value >= 0;
  return (
    <span
      className={`inline-flex items-center gap-1 text-sm font-semibold ${
        positive ? 'text-emerald-300' : 'text-rose-300'
      }`}
    >
      {positive ? '▲' : '▼'} {Math.abs(value).toFixed(2)}{suffix}
    </span>
  );
};

/** Carte KPI comparatif (valeur A → valeur B + évolution). */
const CompareCard = ({ label, valueA, valueB, evolution, formatter = fmtTND }) => (
  <div className="glass-panel p-5 relative overflow-hidden">
    <div className="absolute left-0 top-0 bottom-0 w-1 rounded-l-2xl bg-violet-400/40" />
    <p className="text-xs font-semibold text-violet-400/80 uppercase tracking-widest mb-2 pl-2">
      {label}
    </p>
    <div className="pl-2 flex items-baseline gap-2 flex-wrap">
      <span className="text-violet-200/70 text-sm">{formatter(valueA)}</span>
      <span className="text-violet-400/50">→</span>
      <span className="text-white text-lg font-bold">{formatter(valueB)}</span>
    </div>
    <div className="pl-2 mt-2">
      <EvolutionBadge value={evolution} />
    </div>
  </div>
);

const Advanced = () => {
  // ── Prévisions ──
  const [horizon, setHorizon] = useState(3);
  const [forecastData, setForecastData] = useState(null);
  const [forecastLoading, setForecastLoading] = useState(false);
  const [forecastError, setForecastError] = useState('');

  // ── Comparaison ──
  const [periods, setPeriods] = useState({
    period_a_start: '', period_a_end: '',
    period_b_start: '', period_b_end: '',
  });
  const [compareData, setCompareData] = useState(null);
  const [compareLoading, setCompareLoading] = useState(false);
  const [compareError, setCompareError] = useState('');

  // Charge la prévision
  const loadForecast = useCallback(async (h) => {
    setForecastLoading(true);
    setForecastError('');
    try {
      const data = await fetchForecast(h);
      setForecastData(data);
    } catch (e) {
      setForecastError(e.message || 'Erreur lors de la prévision');
    } finally {
      setForecastLoading(false);
    }
  }, []);

  // Initialisation : plage de dates + prévision par défaut
  useEffect(() => {
    loadForecast(3);
    getDateRange()
      .then(({ min_date, max_date }) => {
        if (!min_date || !max_date) return;
        // Pré-remplissage : A = première moitié, B = seconde moitié
        const start = new Date(min_date);
        const end = new Date(max_date);
        const mid = new Date((start.getTime() + end.getTime()) / 2);
        const iso = (d) => d.toISOString().slice(0, 10);
        const midNext = new Date(mid.getTime() + 86400000);
        setPeriods({
          period_a_start: min_date,
          period_a_end: iso(mid),
          period_b_start: iso(midNext),
          period_b_end: max_date,
        });
      })
      .catch(() => {});
  }, [loadForecast]);

  const handleHorizon = (h) => {
    setHorizon(h);
    loadForecast(h);
  };

  const handleCompare = async () => {
    setCompareLoading(true);
    setCompareError('');
    try {
      const data = await comparePeriods(periods);
      setCompareData(data);
    } catch (e) {
      setCompareError(e.message || 'Erreur lors de la comparaison');
    } finally {
      setCompareLoading(false);
    }
  };

  const setPeriod = (key) => (e) =>
    setPeriods((prev) => ({ ...prev, [key]: e.target.value }));

  const meta = forecastData?.metadata;

  return (
    <div className="min-h-[calc(100vh-4rem)] p-6 max-w-7xl mx-auto">
      {/* En-tête */}
      <motion.div
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.35 }}
        className="mb-8"
      >
        <h1 className="text-3xl font-bold bg-gradient-to-r from-violet-300 via-white to-violet-200 bg-clip-text text-transparent drop-shadow-sm">
          Analyse Avancée
        </h1>
        <p className="mt-2 text-violet-200/90">
          Prévisions de ventes et comparaison de périodes pour anticiper et piloter votre activité
        </p>
      </motion.div>

      {/* ════════════ SECTION 1 — PRÉVISIONS ════════════ */}
      <motion.section
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4, delay: 0.05 }}
        className="mb-10"
      >
        <h2 className="text-xl font-semibold text-violet-100 mb-4 flex items-center gap-2">
          <span className="w-3 h-3 rounded-full bg-violet-400 inline-block" />
          <span>📈</span> Prévision des ventes
        </h2>

        {/* Sélecteur d'horizon */}
        <div className="flex flex-wrap items-center gap-3 mb-5">
          <span className="text-sm text-violet-200/80">Horizon :</span>
          {[3, 6, 12].map((h) => (
            <button
              key={h}
              type="button"
              onClick={() => handleHorizon(h)}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                horizon === h
                  ? 'bg-gradient-to-r from-violet-500 to-purple-500 text-white shadow-lg shadow-violet-900/30'
                  : 'border border-violet-400/30 bg-violet-500/10 text-violet-100 hover:bg-violet-500/20'
              }`}
            >
              {h} mois
            </button>
          ))}
        </div>

        <div className="glass-panel p-6">
          {forecastError && (
            <div className="mb-4 p-4 rounded-xl bg-rose-500/20 border border-rose-400/40 text-rose-100">
              {forecastError}
            </div>
          )}

          {forecastLoading ? (
            <div className="h-72 flex items-center justify-center text-violet-300/70 animate-pulse">
              Calcul de la prévision...
            </div>
          ) : (
            <>
              <ForecastChart
                history={forecastData?.history || []}
                forecast={forecastData?.forecast || []}
              />

              {meta && (
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-6">
                  <div className="text-center">
                    <p className="text-xs text-violet-400/70 uppercase tracking-wide mb-1">Tendance</p>
                    <p className={`text-lg font-bold ${
                      meta.trend === 'croissance' ? 'text-emerald-300'
                        : meta.trend === 'déclin' ? 'text-rose-300' : 'text-violet-200'
                    }`}>
                      {meta.trend === 'croissance' ? '▲ ' : meta.trend === 'déclin' ? '▼ ' : '● '}
                      {meta.trend}
                    </p>
                  </div>
                  <div className="text-center">
                    <p className="text-xs text-violet-400/70 uppercase tracking-wide mb-1">Total prévu</p>
                    <p className="text-lg font-bold text-white">{fmtTND(meta.total_forecast)}</p>
                  </div>
                  <div className="text-center">
                    <p className="text-xs text-violet-400/70 uppercase tracking-wide mb-1">Moy. mensuelle</p>
                    <p className="text-lg font-bold text-violet-200">{fmtTND(meta.avg_historical)}</p>
                  </div>
                  <div className="text-center">
                    <p className="text-xs text-violet-400/70 uppercase tracking-wide mb-1">Fiabilité (R²)</p>
                    <p className="text-lg font-bold text-violet-200">{(meta.r2_score * 100).toFixed(0)}%</p>
                  </div>
                </div>
              )}

              {meta?.peak_month && (
                <p className="mt-4 text-sm text-violet-300/80 text-center">
                  💡 Pic saisonnier détecté au mois de <span className="font-semibold text-violet-200">{meta.peak_month}</span>.
                </p>
              )}
            </>
          )}
        </div>
      </motion.section>

      <div className="h-px bg-gradient-to-r from-transparent via-violet-500/30 to-transparent mb-10" />

      {/* ════════════ SECTION 2 — COMPARAISON ════════════ */}
      <motion.section
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4, delay: 0.1 }}
        className="mb-8"
      >
        <h2 className="text-xl font-semibold text-violet-100 mb-4 flex items-center gap-2">
          <span className="w-3 h-3 rounded-full bg-cyan-400 inline-block" />
          <span>⚖️</span> Comparaison de périodes
        </h2>

        {/* Sélecteurs de dates */}
        <div className="glass-panel p-6 mb-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Période A */}
            <div>
              <p className="text-sm font-semibold text-cyan-300 mb-3">Période A</p>
              <div className="flex flex-col sm:flex-row gap-3">
                <input
                  type="date"
                  value={periods.period_a_start}
                  onChange={setPeriod('period_a_start')}
                  className="flex-1 px-3 py-2 rounded-lg bg-slate-900/60 border border-violet-400/30 text-violet-100 text-sm focus:outline-none focus:border-violet-400"
                />
                <input
                  type="date"
                  value={periods.period_a_end}
                  onChange={setPeriod('period_a_end')}
                  className="flex-1 px-3 py-2 rounded-lg bg-slate-900/60 border border-violet-400/30 text-violet-100 text-sm focus:outline-none focus:border-violet-400"
                />
              </div>
            </div>

            {/* Période B */}
            <div>
              <p className="text-sm font-semibold text-purple-300 mb-3">Période B</p>
              <div className="flex flex-col sm:flex-row gap-3">
                <input
                  type="date"
                  value={periods.period_b_start}
                  onChange={setPeriod('period_b_start')}
                  className="flex-1 px-3 py-2 rounded-lg bg-slate-900/60 border border-violet-400/30 text-violet-100 text-sm focus:outline-none focus:border-violet-400"
                />
                <input
                  type="date"
                  value={periods.period_b_end}
                  onChange={setPeriod('period_b_end')}
                  className="flex-1 px-3 py-2 rounded-lg bg-slate-900/60 border border-violet-400/30 text-violet-100 text-sm focus:outline-none focus:border-violet-400"
                />
              </div>
            </div>
          </div>

          <button
            type="button"
            onClick={handleCompare}
            disabled={compareLoading}
            className="mt-5 px-6 py-3 rounded-xl font-medium text-white
                       bg-gradient-to-r from-violet-500 to-purple-500
                       shadow-lg shadow-violet-900/30
                       hover:ring-2 hover:ring-violet-400/50 hover:ring-offset-1 hover:ring-offset-slate-950
                       disabled:opacity-50 disabled:cursor-not-allowed transition-shadow"
          >
            {compareLoading ? 'Comparaison...' : 'Comparer les périodes'}
          </button>
        </div>

        {compareError && (
          <div className="mb-6 p-4 rounded-xl bg-rose-500/20 border border-rose-400/40 text-rose-100">
            {compareError}
          </div>
        )}

        {compareData && (
          <motion.div
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
          >
            {/* Cartes KPI comparatives */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-6">
              <CompareCard
                label="Chiffre d'affaires"
                valueA={compareData.period_a.kpis.ca_total}
                valueB={compareData.period_b.kpis.ca_total}
                evolution={compareData.evolution.ca_total}
              />
              <CompareCard
                label="Profit total"
                valueA={compareData.period_a.kpis.profit_total}
                valueB={compareData.period_b.kpis.profit_total}
                evolution={compareData.evolution.profit_total}
              />
              <CompareCard
                label="Panier moyen"
                valueA={compareData.period_a.kpis.panier_moyen}
                valueB={compareData.period_b.kpis.panier_moyen}
                evolution={compareData.evolution.panier_moyen}
              />
              <CompareCard
                label="Marge bénéficiaire"
                valueA={compareData.period_a.kpis.marge}
                valueB={compareData.period_b.kpis.marge}
                evolution={compareData.evolution.marge}
                formatter={(v) => `${v.toFixed(1)} %`}
              />
              <CompareCard
                label="Transactions"
                valueA={compareData.period_a.kpis.nb_transactions}
                valueB={compareData.period_b.kpis.nb_transactions}
                evolution={compareData.evolution.nb_transactions}
                formatter={(v) => Math.round(v).toLocaleString('fr-FR')}
              />
            </div>

            {/* Graphique par catégorie */}
            <div className="glass-panel p-6">
              <h3 className="text-lg font-medium text-white mb-4">CA par catégorie</h3>
              <CategoryComparisonChart
                data={compareData.category_comparison}
                labelA={compareData.period_a.label}
                labelB={compareData.period_b.label}
              />
            </div>
          </motion.div>
        )}
      </motion.section>
    </div>
  );
};

export default Advanced;
