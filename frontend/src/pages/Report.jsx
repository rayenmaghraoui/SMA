/**
 * Report — affichage du rapport complet.
 */

import { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import api from '../services/api';
import { toast } from '../services/toast';

/** Séparateur entre sections */
const SectionDivider = () => (
  <div className="h-px bg-gradient-to-r from-transparent via-violet-500/35 to-transparent my-2" />
);

/** Squelette de chargement */
const ReportSkeleton = () => (
  <div className="space-y-8 animate-pulse">
    <div className="glass-panel p-6 space-y-3">
      <div className="h-3 w-32 bg-violet-400/20 rounded-full" />
      <div className="h-4 w-full bg-violet-300/15 rounded" />
      <div className="h-4 w-4/5 bg-violet-300/10 rounded" />
    </div>
    {[1, 2, 3].map((i) => (
      <div key={i} className="glass-panel p-6 flex gap-4">
        <div className="w-16 h-7 bg-violet-400/20 rounded-full flex-shrink-0" />
        <div className="flex-1 space-y-2">
          <div className="h-4 w-2/3 bg-violet-300/20 rounded" />
          <div className="h-3 w-full bg-violet-200/10 rounded" />
        </div>
      </div>
    ))}
  </div>
);

/**
 * Config des badges de priorité.
 */
const PRIORITY_CONFIG = {
  1: { label: 'Critique', bg: 'bg-rose-500/20',   border: 'border-rose-400/40',   text: 'text-rose-300',   dot: 'bg-rose-500' },
  2: { label: 'Haute',    bg: 'bg-orange-500/20',  border: 'border-orange-400/40', text: 'text-orange-300', dot: 'bg-orange-500' },
  3: { label: 'Moyenne',  bg: 'bg-amber-400/20',   border: 'border-amber-400/40',  text: 'text-amber-300',  dot: 'bg-amber-400' },
  4: { label: 'Faible',   bg: 'bg-violet-500/20',  border: 'border-violet-400/40', text: 'text-violet-300', dot: 'bg-violet-500' },
  5: { label: 'Optionnel',bg: 'bg-slate-500/20',   border: 'border-slate-400/40',  text: 'text-slate-300',  dot: 'bg-slate-500' },
};

/**
 * Carte de recommandation.
 */
const RecommendationCard = ({ recommendation, index }) => {
  const cfg = PRIORITY_CONFIG[recommendation.priorite] || PRIORITY_CONFIG[5];

  return (
    <motion.div
      initial={{ opacity: 0, x: -20 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ delay: index * 0.08 }}
      className="glass-panel p-6 hover:ring-1 hover:ring-violet-400/25 transition-shadow"
    >
      <div className="flex items-start gap-4">
        {/* Badge de priorité avec label */}
        <div className={`flex-shrink-0 flex items-center gap-2 px-3 py-1.5 rounded-full border ${cfg.bg} ${cfg.border}`}>
          <span className={`w-2 h-2 rounded-full ${cfg.dot} flex-shrink-0`} />
          <span className={`text-xs font-semibold tracking-wide ${cfg.text}`}>{cfg.label}</span>
        </div>
        <div className="flex-1">
          <h3 className="text-base font-semibold text-white leading-snug">
            {recommendation.titre}
          </h3>
          <p className="mt-2 text-violet-100/85 text-sm leading-relaxed">
            {recommendation.action}
          </p>
          <div className="mt-3 flex flex-wrap gap-2">
            {recommendation.impact && (
              <span className="px-2.5 py-1 rounded-full text-xs text-emerald-200 bg-emerald-500/20 border border-emerald-400/30">
                Impact: {recommendation.impact}
              </span>
            )}
            {recommendation.source && (
              <span className="px-2.5 py-1 rounded-full text-xs text-violet-200 bg-violet-500/15 border border-violet-400/25">
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
  const [isExporting, setIsExporting] = useState(false);

  // Télécharge le rapport PDF généré côté serveur (reportlab)
  const handleExportPdf = async () => {
    if (isExporting) return;
    setIsExporting(true);
    try {
      const response = await api.get('/report/pdf', { responseType: 'blob' });
      const url = URL.createObjectURL(response.data);
      const a = document.createElement('a');
      a.href = url;
      a.download = `rapport_ai_business_consultant_${new Date().toISOString().slice(0, 10)}.pdf`;
      a.click();
      URL.revokeObjectURL(url);
      toast.success('Rapport PDF téléchargé.');
    } catch (err) {
      console.error('Erreur export PDF:', err);
      toast.error('Échec de la génération du PDF. Réessayez.');
    } finally {
      setIsExporting(false);
    }
  };

  useEffect(() => {
    const fetchReport = async () => {
      try {
        const response = await api.get('/report/latest');
        if (response.data?.success && response.data?.has_report) {
          setReport(response.data.report);
        } else {
          setError("Aucun rapport disponible. Lancez d'abord une analyse.");
        }
      } catch (err) {
        setError(err.response?.data?.detail || 'Erreur lors du chargement');
      } finally {
        setIsLoading(false);
      }
    };

    fetchReport();
  }, []);

  if (isLoading) {
    return (
      <div className="min-h-[calc(100vh-4rem)] p-6">
        <div className="mb-8">
          <div className="h-8 w-56 bg-violet-400/20 rounded-lg animate-pulse mb-3" />
          <div className="h-3 w-40 bg-violet-300/15 rounded animate-pulse" />
        </div>
        <ReportSkeleton />
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-[calc(100vh-4rem)] flex items-center justify-center p-6">
        <motion.div
          initial={{ opacity: 0, scale: 0.97 }}
          animate={{ opacity: 1, scale: 1 }}
          className="text-center glass-panel p-10 max-w-md flex flex-col items-center gap-4"
        >
          <div className="w-20 h-20 rounded-full bg-violet-500/10 border border-violet-400/20 flex items-center justify-center">
            <svg className="w-10 h-10 text-violet-400/70" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
                d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
          </div>
          <div>
            <h3 className="text-lg font-semibold text-white mb-2">Rapport indisponible</h3>
            <p className="text-violet-200/80 text-sm">{error}</p>
          </div>
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
          <h1 className="text-3xl font-bold bg-gradient-to-r from-violet-300 via-white to-violet-200 bg-clip-text text-transparent">
            Rapport d&apos;Analyse
          </h1>
          <p className="mt-2 text-violet-200/90">
            Généré le {new Date(report?.metadata?.date_generation).toLocaleString('fr-FR')}
          </p>
        </div>
        <motion.button
          type="button"
          onClick={handleExportPdf}
          disabled={isExporting}
          className="no-print px-4 py-2 rounded-xl text-white bg-violet-500/25 border border-violet-400/30
                     hover:bg-violet-500/40 transition-colors flex items-center justify-center gap-2 w-fit
                     hover:ring-2 hover:ring-violet-400/40 hover:ring-offset-1 hover:ring-offset-slate-950
                     disabled:opacity-60 disabled:cursor-not-allowed"
          whileHover={isExporting ? {} : { scale: 1.03 }}
          whileTap={isExporting ? {} : { scale: 0.98 }}
        >
          {isExporting ? (
            <svg className="w-5 h-5 animate-spin" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
            </svg>
          ) : (
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
          )}
          {isExporting ? 'Génération…' : 'Exporter PDF'}
        </motion.button>
      </motion.div>

      <section className="mb-6">
        <h2 className="text-xl font-semibold text-violet-100 mb-4 flex items-center gap-2">
          <span>📋</span> Résumé Exécutif
        </h2>
        <div className="glass-panel p-6">
          <p className="text-violet-100/95 leading-relaxed text-lg">
            {report?.resume_executif}
          </p>
        </div>
      </section>

      <SectionDivider />

      {report?.interpretation && (
        <section className="mb-6">
          <h2 className="text-xl font-semibold text-violet-100 mb-4 flex items-center gap-2">
            <span>🧠</span> Analyse Détaillée
          </h2>
          <div className="glass-panel p-6">
            <div className="max-w-none">
              {report.interpretation.split('\n').map((paragraph, i) => (
                <p key={i} className="mb-4 text-violet-100/90 leading-relaxed">
                  {paragraph}
                </p>
              ))}
            </div>
          </div>
        </section>
      )}

      <SectionDivider />

      <section className="mb-6">
        <h2 className="text-xl font-semibold text-violet-100 mb-4 flex items-center gap-2">
          <span>💡</span> Recommandations Stratégiques
        </h2>
        <div className="space-y-4">
          {report?.recommendations?.map((rec, index) => (
            <RecommendationCard key={index} recommendation={rec} index={index} />
          ))}
        </div>
      </section>

      <SectionDivider />

      {report?.anomalies?.total > 0 && (
        <section className="mb-6">
          <h2 className="text-xl font-semibold text-violet-100 mb-4 flex items-center gap-2">
            <span>⚠️</span> Anomalies Détectées ({report.anomalies.total})
          </h2>
          <div className="glass-panel p-6 overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-violet-500/20">
                  <th className="text-left py-3 px-4 text-violet-300/90">Dataset</th>
                  <th className="text-left py-3 px-4 text-violet-300/90">Colonne</th>
                  <th className="text-left py-3 px-4 text-violet-300/90">Valeur</th>
                  <th className="text-left py-3 px-4 text-violet-300/90">Type</th>
                </tr>
              </thead>
              <tbody>
                {report.anomalies.details.slice(0, 10).map((anomaly, i) => (
                  <tr key={i} className="border-b border-violet-500/10 last:border-0">
                    <td className="py-3 px-4 capitalize text-violet-100">{anomaly.dataset}</td>
                    <td className="py-3 px-4 text-violet-100">{anomaly.colonne}</td>
                    <td className="py-3 px-4 font-mono text-violet-200">{anomaly.valeur}</td>
                    <td className="py-3 px-4">
                      <span className={`px-2 py-1 rounded text-sm ${
                        anomaly.type === 'high'
                          ? 'bg-rose-500/25 text-rose-200 border border-rose-400/35'
                          : 'bg-violet-500/20 text-violet-100 border border-violet-400/30'
                      }`}>
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

      <SectionDivider />

      {report?.sources_rag?.length > 0 && (
        <section className="mb-6">
          <h2 className="text-xl font-semibold text-violet-100 mb-4 flex items-center gap-2">
            <span>📚</span> Sources Consultées
          </h2>
          <div className="glass-panel p-6">
            <div className="space-y-2">
              {report.sources_rag.map((source, i) => (
                <div key={i} className="flex items-center gap-2 text-violet-100/90">
                  <svg className="w-4 h-4 text-violet-400 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                  <span>{source.document}</span>
                  {source.section && (
                    <span className="text-violet-400/70">— {source.section}</span>
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
