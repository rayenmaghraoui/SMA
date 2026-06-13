import { useEffect, useRef, useState } from 'react';
import { motion } from 'framer-motion';
import { Link } from 'react-router-dom';
import KpiCard, { AnimatedNumber } from '../components/KpiCard';
import { ChannelChart, DistributionChart } from '../components/Charts';
import AgentProgress from '../components/AgentProgress';
import useAnalysis from '../hooks/useAnalysis';

/* ──────────────────────────────────────────────────────
   Squelettes de chargement
────────────────────────────────────────────────────── */
const KpiSkeleton = () => (
  <div className="glass-panel p-6 animate-pulse relative overflow-hidden">
    <div className="absolute left-0 top-0 bottom-0 w-1 rounded-l-2xl bg-violet-400/25" />
    <div className="pl-2 space-y-3">
      <div className="h-2.5 w-28 bg-violet-400/20 rounded-full" />
      <div className="h-8 w-24 bg-violet-300/15 rounded-lg" />
    </div>
  </div>
);

const SectionSkeleton = () => (
  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
    {[...Array(4)].map((_, i) => <KpiSkeleton key={i} />)}
  </div>
);

/* ──────────────────────────────────────────────────────
   Badge de priorité recommandation (priorite = 1–5)
────────────────────────────────────────────────────── */
const PRIORITY_MAP = {
  1: { label: 'CRITIQUE', cls: 'bg-rose-500/20 border-rose-400/50 text-rose-300' },
  2: { label: 'HAUTE',    cls: 'bg-orange-500/20 border-orange-400/50 text-orange-300' },
  3: { label: 'MOYENNE',  cls: 'bg-amber-500/20 border-amber-400/50 text-amber-300' },
  4: { label: 'BASSE',    cls: 'bg-blue-500/20 border-blue-400/50 text-blue-300' },
  5: { label: 'INFO',     cls: 'bg-slate-500/20 border-slate-400/50 text-slate-300' },
};

const PriorityBadge = ({ priorite }) => {
  const p = PRIORITY_MAP[priorite] || PRIORITY_MAP[3];
  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-md text-xs font-bold border shrink-0 ${p.cls}`}>
      {p.label}
    </span>
  );
};

/* ──────────────────────────────────────────────────────
   Cards de navigation rapide
────────────────────────────────────────────────────── */
const NAV_CARDS = [
  {
    to: '/chat',
    color: 'violet',
    title: 'Poser une question',
    desc: 'Assistant IA en langage naturel',
    icon: (
      <svg className="w-5 h-5 text-violet-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.8}
          d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
      </svg>
    ),
  },
  {
    to: '/report',
    color: 'emerald',
    title: 'Voir le rapport',
    desc: 'Recommandations & anomalies détaillées',
    icon: (
      <svg className="w-5 h-5 text-emerald-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.8}
          d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
      </svg>
    ),
  },
  {
    to: '/advanced',
    color: 'blue',
    title: 'Analyse avancée',
    desc: 'Prévision des ventes & comparaison',
    icon: (
      <svg className="w-5 h-5 text-blue-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.8}
          d="M7 12l3-3 3 3 4-4M8 21l4-4 4 4M3 4h18M4 4h16v12a1 1 0 01-1 1H5a1 1 0 01-1-1V4z" />
      </svg>
    ),
  },
];

const QuickNavCard = ({ to, color, title, desc, icon }) => (
  <motion.div whileHover={{ y: -4, scale: 1.02 }} whileTap={{ scale: 0.98 }} transition={{ type: 'spring', stiffness: 400, damping: 25 }}>
    <Link to={to} className="block glass-panel p-5 hover:ring-2 hover:ring-violet-400/40 hover:ring-offset-1 hover:ring-offset-slate-950 transition-shadow h-full">
      <div className={`w-10 h-10 rounded-xl bg-${color}-500/15 border border-${color}-400/30 flex items-center justify-center mb-3`}>
        {icon}
      </div>
      <h3 className="text-sm font-semibold text-white mb-1">{title}</h3>
      <p className="text-xs text-violet-300/60">{desc}</p>
    </Link>
  </motion.div>
);

/* ──────────────────────────────────────────────────────
   Page Dashboard
────────────────────────────────────────────────────── */
const Dashboard = () => {
  const { kpis, report, isLoading, error, initialLoadDone, fetchReport, triggerAnalysis } = useAnalysis();
  const autoTriggered = useRef(false);
  const [dashStep, setDashStep] = useState('');

  useEffect(() => { fetchReport(); }, [fetchReport]);

  useEffect(() => {
    if (initialLoadDone && !isLoading && Object.keys(kpis).length === 0 && !autoTriggered.current) {
      autoTriggered.current = true;
      triggerAnalysis(true);
    }
  }, [initialLoadDone, isLoading, kpis, triggerAnalysis]);

  useEffect(() => {
    if (!isLoading) { setDashStep(''); return; }
    const steps = ['analysis_agent', 'interpretation_agent', 'rag_agent', 'recommendation_agent', 'report_agent'];
    let i = 0;
    setDashStep(steps[0]);
    const timer = setInterval(() => {
      i = Math.min(i + 1, steps.length - 1);
      setDashStep(steps[i]);
    }, 8000);
    return () => clearInterval(timer);
  }, [isLoading]);

  const financeKpis    = kpis.finance?.indicateurs    || [];
  const marketingKpis  = kpis.marketing?.indicateurs  || [];
  const categoriesKpis = kpis.categories?.indicateurs || [];
  const hasData        = Object.keys(kpis).length > 0;

  /* Donut catégories */
  const categoryDonutData = kpis.categories?.revenue_par_categorie
    ? Object.entries(kpis.categories.revenue_par_categorie)
        .map(([name, value]) => ({ name, value: Number(value) }))
        .sort((a, b) => b.value - a.value)
    : [];

  /* Top 2 recommandations */
  const topRecs = report?.recommendations?.slice(0, 2) || [];

  /* Nb anomalies */
  const nbAnomalies = report?.anomalies?.total ?? 0;

  return (
    <div className="min-h-[calc(100vh-4rem)] p-6">

      {/* ── En-tête ── */}
      <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.35 }} className="mb-8">
        <h1 className="text-3xl font-bold bg-gradient-to-r from-violet-300 via-white to-violet-200 bg-clip-text text-transparent drop-shadow-sm">
          Tableau de Bord
        </h1>
        <p className="mt-2 text-violet-200/90">
          Vue d&apos;ensemble des performances de votre entreprise
          {report?.metadata?.date_generation && (
            <span className="ml-3 text-xs text-violet-400/70">
              · Mise à jour : {new Date(report.metadata.date_generation).toLocaleString('fr-FR', { day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit' })}
            </span>
          )}
        </p>
      </motion.div>

      {/* ── Actions + Navigation rapide ── */}
      <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.1 }} className="mb-8">
        <div className="flex flex-wrap gap-3 mb-5">
          <motion.button
            type="button"
            onClick={() => triggerAnalysis(true, hasData)}
            disabled={isLoading}
            className="px-6 py-3 rounded-xl font-medium text-white
                       bg-gradient-to-r from-violet-500 to-purple-500
                       shadow-lg shadow-violet-900/30
                       hover:ring-2 hover:ring-violet-400/50 hover:ring-offset-1 hover:ring-offset-slate-950
                       disabled:opacity-50 disabled:cursor-not-allowed transition-shadow"
            whileHover={{ scale: isLoading ? 1 : 1.03 }}
            whileTap={{ scale: isLoading ? 1 : 0.98 }}
          >
            {isLoading ? 'Analyse en cours...' : hasData ? 'Ré-analyser' : 'Lancer l\'analyse'}
          </motion.button>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          {NAV_CARDS.map((card) => <QuickNavCard key={card.to} {...card} />)}
        </div>
      </motion.div>

      {/* ── Erreur ── */}
      {error && (
        <motion.div initial={{ opacity: 0, x: -8 }} animate={{ opacity: 1, x: 0 }}
          className="mb-8 p-4 rounded-xl bg-rose-500/20 border border-rose-400/40 text-rose-100">
          {error}
        </motion.div>
      )}

      {/* ── Chargement ── */}
      {isLoading && (
        <div className="space-y-6 mb-8">
          <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} className="glass-panel p-6">
            <p className="text-sm text-violet-300/80 text-center mb-5">
              {dashStep ? 'Pipeline multi-agents en cours...' : 'Démarrage de l\'analyse...'}
            </p>
            <AgentProgress currentStep={dashStep} isLoading={isLoading} />
          </motion.div>
          <SectionSkeleton />
          <SectionSkeleton />
        </div>
      )}

      {/* ── Aucune donnée ── */}
      {!isLoading && !hasData && (
        <motion.div initial={{ opacity: 0, scale: 0.97 }} animate={{ opacity: 1, scale: 1 }}
          className="mb-8 glass-panel p-12 text-center flex flex-col items-center gap-4">
          <div className="relative">
            <div className="w-24 h-24 rounded-full bg-violet-500/10 border border-violet-400/20 flex items-center justify-center">
              <svg className="w-12 h-12 text-violet-400/70" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
                  d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
              </svg>
            </div>
            <motion.div className="absolute -top-1 -right-1 w-5 h-5 rounded-full bg-violet-500/40 border border-violet-400/30"
              animate={{ scale: [1, 1.3, 1], opacity: [0.6, 1, 0.6] }} transition={{ duration: 2, repeat: Infinity }} />
          </div>
          <div>
            <h2 className="text-xl font-semibold text-white mb-2">Aucune analyse disponible</h2>
            <p className="text-violet-200/80 max-w-sm mx-auto">
              Cliquez sur <span className="text-violet-300 font-medium">Lancer l&apos;analyse</span> pour calculer les KPIs
              et générer les recommandations stratégiques.
            </p>
          </div>
        </motion.div>
      )}

      {/* ══════════════════════════════════════════════
          DONNÉES DISPONIBLES
      ══════════════════════════════════════════════ */}
      {!isLoading && hasData && (
        <>
          {/* ── Hero KPI + Badge anomalies ── */}
          {(() => {
            const fi  = kpis.finance?.indicateurs || [];
            const ca     = fi.find(i => i.label?.includes('CA Total') || i.label?.includes('Chiffre'));
            const profit = fi.find(i => i.label?.includes('Profit'));
            const marge  = fi.find(i => i.label?.includes('Marge'));
            const txns   = fi.find(i => i.label?.includes('Transaction') || i.label?.includes('Nb Trans'));
            if (!ca) return null;
            return (
              <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.4 }}
                className="mb-6 glass-panel p-8 relative overflow-hidden">
                <div className="absolute inset-0 bg-gradient-to-br from-violet-600/10 via-transparent to-purple-600/5 pointer-events-none" />
                <div className="absolute -top-10 -right-10 w-48 h-48 rounded-full bg-violet-500/10 blur-3xl pointer-events-none" />

                {/* Badge anomalies */}
                {nbAnomalies > 0 && (
                  <Link to="/report"
                    className="absolute top-4 right-4 flex items-center gap-2 bg-rose-500/20 border border-rose-400/40 rounded-lg px-3 py-1.5 hover:bg-rose-500/30 transition-colors">
                    <span className="w-2 h-2 rounded-full bg-rose-400 animate-pulse" />
                    <span className="text-rose-200 text-xs font-semibold">
                      {nbAnomalies} anomalie{nbAnomalies > 1 ? 's' : ''} détectée{nbAnomalies > 1 ? 's' : ''}
                    </span>
                    <span className="text-rose-400 text-xs">→</span>
                  </Link>
                )}

                <p className="text-xs font-semibold text-violet-400/80 uppercase tracking-widest mb-1">
                  Chiffre d&apos;Affaires Total
                </p>
                <p className="text-5xl font-extrabold text-white mb-4">
                  <AnimatedNumber value={ca.valeur} format={ca.format} unite={ca.unite} />
                </p>
                <div className="flex flex-wrap gap-6 text-sm">
                  {profit && (
                    <div>
                      <span className="text-violet-400/70 block text-xs mb-0.5">Bénéfice</span>
                      <span className="text-emerald-300 font-semibold">
                        <AnimatedNumber value={profit.valeur} format={profit.format} unite={profit.unite} />
                      </span>
                    </div>
                  )}
                  {marge && (
                    <div>
                      <span className="text-violet-400/70 block text-xs mb-0.5">Marge</span>
                      <span className="text-violet-200 font-semibold">
                        <AnimatedNumber value={marge.valeur} format={marge.format} unite={marge.unite} />
                      </span>
                    </div>
                  )}
                  {txns && (
                    <div>
                      <span className="text-violet-400/70 block text-xs mb-0.5">Transactions</span>
                      <span className="text-violet-200 font-semibold">
                        <AnimatedNumber value={txns.valeur} format={txns.format} unite={txns.unite} />
                      </span>
                    </div>
                  )}
                </div>
              </motion.div>
            );
          })()}

          {/* ── Finance ── */}
          <section className="mb-6">
            <h2 className="text-xl font-semibold text-violet-100 mb-4 flex items-center gap-2">
              <span className="w-3 h-3 rounded-full bg-emerald-400 inline-block" />
              <span>💰</span> Performance Financière
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              {financeKpis.map((kpi, index) => (
                <motion.div key={kpi.label} initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: index * 0.08 }}>
                  <KpiCard label={kpi.label} value={kpi.valeur} format={kpi.format} unite={kpi.unite}
                    trend={kpi.label.includes('Tendance') ? kpi.valeur : null} accentColor="emerald" />
                </motion.div>
              ))}
            </div>
          </section>

          <div className="h-px bg-gradient-to-r from-transparent via-violet-500/30 to-transparent mb-6" />

          {/* ── Canaux ── */}
          <section className="mb-6">
            <h2 className="text-xl font-semibold text-violet-100 mb-4 flex items-center gap-2">
              <span className="w-3 h-3 rounded-full bg-blue-400 inline-block" />
              <span>📡</span> Performance Canaux de Vente
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              {marketingKpis.map((kpi, index) => (
                <motion.div key={kpi.label} initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: index * 0.08 }}>
                  <KpiCard label={kpi.label} value={kpi.valeur} format={kpi.format} unite={kpi.unite} accentColor="blue" />
                </motion.div>
              ))}
            </div>
            {kpis.marketing?.ca_par_canal && (
              <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} className="mt-6 glass-panel p-6">
                <h3 className="text-lg font-medium text-white mb-4">CA par Canal</h3>
                <ChannelChart data={kpis.marketing.ca_par_canal} />
              </motion.div>
            )}
          </section>

          <div className="h-px bg-gradient-to-r from-transparent via-violet-500/30 to-transparent mb-6" />

          {/* ── Catégories + Donut ── */}
          <section className="mb-6">
            <h2 className="text-xl font-semibold text-violet-100 mb-4 flex items-center gap-2">
              <span className="w-3 h-3 rounded-full bg-amber-400 inline-block" />
              <span>📦</span> Performance par Catégorie
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              {categoriesKpis.map((kpi, index) => (
                <motion.div key={kpi.label} initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: index * 0.08 }}>
                  <KpiCard label={kpi.label} value={kpi.valeur} format={kpi.format} unite={kpi.unite} accentColor="amber" />
                </motion.div>
              ))}
            </div>
            {categoryDonutData.length > 0 && (
              <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} className="mt-6 glass-panel p-6">
                <h3 className="text-lg font-medium text-white mb-4">Répartition CA par Catégorie</h3>
                <DistributionChart data={categoryDonutData} nameKey="name" valueKey="value" />
              </motion.div>
            )}
          </section>

          <div className="h-px bg-gradient-to-r from-transparent via-violet-500/30 to-transparent mb-6" />

          {/* ── Interprétation IA ── */}
          {report?.interpretation && (
            <motion.section initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} className="mb-6">
              <h2 className="text-xl font-semibold text-violet-100 mb-4 flex items-center gap-2">
                <span>🤖</span> Interprétation IA
              </h2>
              <div className="glass-panel p-6 border-l-2 border-violet-500/50">
                <p className="text-slate-100/90 leading-relaxed whitespace-pre-line text-sm">
                  {report.interpretation}
                </p>
              </div>
            </motion.section>
          )}

          {/* ── Top Recommandations ── */}
          {topRecs.length > 0 && (
            <motion.section initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} className="mb-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-xl font-semibold text-violet-100 flex items-center gap-2">
                  <span>⚡</span> Recommandations Prioritaires
                </h2>
                <Link to="/report" className="text-sm text-violet-400 hover:text-violet-300 transition-colors">
                  Voir toutes →
                </Link>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {topRecs.map((rec, i) => (
                  <motion.div key={i} initial={{ opacity: 0, x: i === 0 ? -12 : 12 }} animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: i * 0.1 }}
                    className="glass-panel p-5 hover:ring-2 hover:ring-violet-400/30 transition-shadow">
                    <div className="flex items-start gap-3">
                      <PriorityBadge priorite={rec.priorite} />
                      <div className="flex-1 min-w-0">
                        <h4 className="text-white font-semibold text-sm mb-1 leading-snug">{rec.titre}</h4>
                        <p className="text-violet-200/70 text-xs leading-relaxed line-clamp-2">{rec.action}</p>
                        {rec.impact && (
                          <p className="mt-2 text-emerald-400/80 text-xs font-medium">
                            Impact : {rec.impact}
                          </p>
                        )}
                      </div>
                    </div>
                  </motion.div>
                ))}
              </div>
            </motion.section>
          )}

          {/* ── Résumé exécutif ── */}
          {report?.resume_executif && (
            <section className="mb-8">
              <h2 className="text-xl font-semibold text-violet-100 mb-4 flex items-center gap-2">
                <span>📋</span> Résumé Exécutif
              </h2>
              <div className="glass-panel p-6">
                <p className="text-slate-100/95 leading-relaxed">{report.resume_executif}</p>
              </div>
            </section>
          )}
        </>
      )}
    </div>
  );
};

export default Dashboard;
