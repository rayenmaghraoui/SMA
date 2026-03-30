/**
 * AgentProgress — barre de progression des agents.
 */

import { motion } from 'framer-motion';

/**
 * Liste des étapes du pipeline.
 */
const PIPELINE_STEPS = [
  { key: 'analysis_agent', label: 'Analyse', icon: '📊' },
  { key: 'interpretation_agent', label: 'Interprétation', icon: '🧠' },
  { key: 'rag_agent', label: 'Recherche', icon: '📚' },
  { key: 'recommendation_agent', label: 'Recommandations', icon: '💡' },
  { key: 'report_agent', label: 'Rapport', icon: '📋' },
];

/**
 * Trouve l'index de l'étape courante.
 */
const getStepIndex = (currentStep) => {
  if (!currentStep) return -1;

  // Chercher par clé exacte
  const exactIndex = PIPELINE_STEPS.findIndex((s) => s.key === currentStep);
  if (exactIndex !== -1) return exactIndex;

  // Chercher par contenu partiel
  const stepLower = currentStep.toLowerCase();
  if (stepLower.includes('analyse') || stepLower.includes('analysis')) return 0;
  if (stepLower.includes('interprét') || stepLower.includes('interpret')) return 1;
  if (stepLower.includes('recherche') || stepLower.includes('rag')) return 2;
  if (stepLower.includes('recommand') || stepLower.includes('recommendation')) return 3;
  if (stepLower.includes('rapport') || stepLower.includes('report')) return 4;
  if (stepLower.includes('démarrage') || stepLower.includes('start')) return 0;

  return -1;
};

/**
 * Composant AgentProgress.
 */
const AgentProgress = ({ currentStep, isLoading = false }) => {
  const currentIndex = getStepIndex(currentStep);

  return (
    <div className="w-full">
      {/* Message d'étape */}
      {isLoading && currentStep && (
        <motion.p
          key={currentStep}
          initial={{ opacity: 0, y: -5 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center text-sm font-medium text-blue-600 mb-4"
        >
          {currentStep}
        </motion.p>
      )}

      {/* Barre de progression */}
      <div className="flex items-center justify-between">
        {PIPELINE_STEPS.map((step, index) => {
          const isCompleted = index < currentIndex;
          const isCurrent = index === currentIndex;
          const isPending = index > currentIndex;

          return (
            <div key={step.key} className="flex flex-col items-center flex-1">
              {/* Ligne de connexion (sauf pour le premier) */}
              {index > 0 && (
                <div className="absolute h-0.5 w-full -z-10" style={{ left: '-50%' }}>
                  <div
                    className={`h-full transition-all duration-500 ${
                      isCompleted ? 'bg-green-500' : 'bg-gray-200'
                    }`}
                  />
                </div>
              )}

              {/* Cercle d'étape */}
              <motion.div
                animate={{
                  scale: isCurrent ? 1.1 : 1,
                  boxShadow: isCurrent ? '0 0 0 4px rgba(59, 130, 246, 0.3)' : 'none',
                }}
                className={`relative w-12 h-12 rounded-full flex items-center justify-center text-xl transition-colors ${
                  isCompleted
                    ? 'bg-green-500 text-white'
                    : isCurrent
                    ? 'bg-blue-500 text-white'
                    : 'bg-gray-200 text-gray-500'
                }`}
              >
                {isCompleted ? (
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                ) : (
                  <span>{step.icon}</span>
                )}

                {/* Animation de chargement */}
                {isCurrent && isLoading && (
                  <motion.div
                    className="absolute inset-0 rounded-full border-2 border-blue-300"
                    animate={{ rotate: 360 }}
                    transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
                    style={{ borderTopColor: 'transparent' }}
                  />
                )}
              </motion.div>

              {/* Label */}
              <p
                className={`mt-2 text-xs font-medium text-center ${
                  isCompleted || isCurrent ? 'text-gray-900' : 'text-gray-400'
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
