/**
 * AgentProgress — barre de progression des agents.
 */

import { motion } from 'framer-motion';

/**
 * Liste des étapes du pipeline.
 */
const PIPELINE_STEPS = [
  { key: 'analysis_agent',        label: 'Analyse',          icon: '📊' },
  { key: 'interpretation_agent',  label: 'Interprétation',   icon: '🧠' },
  { key: 'rag_agent',             label: 'Recherche',        icon: '📚' },
  { key: 'recommendation_agent',  label: 'Recommandations',  icon: '💡' },
  { key: 'report_agent',          label: 'Rapport',          icon: '📋' },
];

/**
 * Trouve l'index de l'étape courante.
 */
const getStepIndex = (currentStep) => {
  if (!currentStep) return -1;

  const exactIndex = PIPELINE_STEPS.findIndex((s) => s.key === currentStep);
  if (exactIndex !== -1) return exactIndex;

  const stepLower = currentStep.toLowerCase();
  if (stepLower.includes('analyse') || stepLower.includes('analysis'))         return 0;
  if (stepLower.includes('interprét') || stepLower.includes('interpret'))      return 1;
  if (stepLower.includes('recherche') || stepLower.includes('rag'))            return 2;
  if (stepLower.includes('recommand') || stepLower.includes('recommendation')) return 3;
  if (stepLower.includes('rapport') || stepLower.includes('report'))           return 4;
  if (stepLower.includes('démarrage') || stepLower.includes('start'))          return 0;

  return -1;
};

/**
 * Composant AgentProgress.
 */
const AgentProgress = ({ currentStep, isLoading = false }) => {
  const currentIndex = getStepIndex(currentStep);

  return (
    <div className="w-full">
      {isLoading && currentStep && (
        <motion.p
          key={currentStep}
          initial={{ opacity: 0, y: -5 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center text-sm font-medium text-violet-200 mb-4"
        >
          {currentStep}
        </motion.p>
      )}

      <div className="flex items-center justify-between">
        {PIPELINE_STEPS.map((step, index) => {
          const isCompleted = index < currentIndex;
          const isCurrent   = index === currentIndex;

          return (
            <div key={step.key} className="flex flex-col items-center flex-1 relative">
              {index > 0 && (
                <div
                  className="absolute h-0.5 top-6 -translate-y-1/2 left-0 right-1/2 -z-10 w-full"
                  style={{ marginLeft: '-50%' }}
                >
                  <div
                    className={`h-full transition-all duration-500 rounded-full ${
                      isCompleted
                        ? 'bg-gradient-to-r from-emerald-400 to-violet-400'
                        : 'bg-slate-700/60'
                    }`}
                  />
                </div>
              )}

              <motion.div
                animate={{
                  scale: isCurrent ? 1.08 : 1,
                  boxShadow: isCurrent ? '0 0 0 4px rgba(139, 92, 246, 0.35)' : 'none',
                }}
                className={`relative w-12 h-12 rounded-full flex items-center justify-center text-xl transition-colors ${
                  isCompleted
                    ? 'bg-gradient-to-br from-emerald-400 to-teal-500 text-white'
                    : isCurrent
                    ? 'bg-gradient-to-br from-violet-500 to-purple-600 text-white'
                    : 'bg-slate-800/70 text-violet-500 border border-slate-600/50'
                }`}
              >
                {isCompleted ? (
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                ) : (
                  <span>{step.icon}</span>
                )}

                {isCurrent && isLoading && (
                  <motion.div
                    className="absolute inset-0 rounded-full border-2 border-violet-300/60"
                    animate={{ rotate: 360 }}
                    transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
                    style={{ borderTopColor: 'transparent' }}
                  />
                )}
              </motion.div>

              <p
                className={`mt-2 text-xs font-medium text-center max-w-[72px] leading-tight ${
                  isCompleted || isCurrent ? 'text-violet-100' : 'text-slate-500'
                }`}
              >
                {step.label}
              </p>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default AgentProgress;
