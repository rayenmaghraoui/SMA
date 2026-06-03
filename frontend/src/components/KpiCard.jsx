/**
 * KpiCard — carte d'affichage d'un KPI.
 * Amélioration : stripe colorée à gauche selon le domaine + ring au hover.
 */

import { useEffect, useState } from 'react';
import { motion, animate } from 'framer-motion';

/**
 * Formate une valeur selon son type.
 */
const formatValue = (value, format, unite) => {
  if (value === null || value === undefined || value === 'N/A') {
    return 'N/A';
  }

  switch (format) {
    case 'currency':
      return `${Number(value).toLocaleString('fr-TN')} ${unite || 'TND'}`;
    case 'percent':
      return `${Number(value).toFixed(1)}${unite || '%'}`;
    case 'rating':
      return `${Number(value).toFixed(1)}${unite || '/5'}`;
    case 'duration':
      return `${Number(value).toFixed(1)} ${unite || 'h'}`;
    case 'number':
      return Number(value).toLocaleString('fr-TN');
    default:
      return String(value);
  }
};

/**
 * Nombre animé de 0 → valeur cible au montage.
 * Ignore les valeurs non-numériques (texte, N/A…).
 */
const AnimatedNumber = ({ value, format, unite }) => {
  const target = parseFloat(String(value ?? '').replace(/[^0-9.-]/g, ''));
  const [display, setDisplay] = useState(() => formatValue(value, format, unite));

  useEffect(() => {
    if (isNaN(target) || format === 'text') {
      setDisplay(formatValue(value, format, unite));
      return;
    }
    const ctrl = animate(0, target, {
      duration: 0.9,
      ease: 'easeOut',
      onUpdate: (v) => setDisplay(formatValue(v, format, unite)),
    });
    return ctrl.stop;
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [target]);

  return <span>{display}</span>;
};

/**
 * Détermine la couleur de tendance.
 */
const getTrendColor = (trend, inverse = false) => {
  if (trend === 'hausse' || trend === 'up') {
    return inverse ? 'text-rose-400' : 'text-emerald-400';
  }
  if (trend === 'baisse' || trend === 'down') {
    return inverse ? 'text-emerald-400' : 'text-rose-400';
  }
  return 'text-violet-300';
};

/**
 * Icône de tendance.
 */
const TrendIcon = ({ trend }) => {
  if (trend === 'hausse' || trend === 'up') {
    return (
      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 10l7-7m0 0l7 7m-7-7v18" />
      </svg>
    );
  }
  if (trend === 'baisse' || trend === 'down') {
    return (
      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 14l-7 7m0 0l-7-7m7 7V3" />
      </svg>
    );
  }
  return (
    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 12h14" />
    </svg>
  );
};

/**
 * Stripe colorée à gauche selon le domaine.
 * accentColor : 'emerald' | 'blue' | 'amber' | 'violet' | 'rose'
 */
const ACCENT_STRIPE = {
  emerald: 'bg-emerald-400/80',
  blue:    'bg-blue-400/80',
  amber:   'bg-amber-400/80',
  violet:  'bg-violet-400/80',
  rose:    'bg-rose-400/80',
};

/**
 * Composant KpiCard.
 */
const KpiCard = ({
  label,
  value,
  format = 'text',
  unite = '',
  trend = null,
  inverseTrend = false,
  icon = null,
  accentColor = 'violet',
  className = '',
}) => {
  const stripe = ACCENT_STRIPE[accentColor] || ACCENT_STRIPE.violet;

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      whileHover={{
        y: -4,
        transition: { type: 'spring', stiffness: 400, damping: 25 },
      }}
      className={`glass-panel p-6 border-violet-500/20 relative overflow-hidden
                  hover:ring-2 hover:ring-violet-400/40 hover:ring-offset-1 hover:ring-offset-slate-950
                  transition-shadow ${className}`}
    >
      {/* Stripe colorée à gauche */}
      <div className={`absolute left-0 top-0 bottom-0 w-1 rounded-l-2xl ${stripe}`} />

      <div className="flex items-center justify-between">
        <div className="flex-1 pl-2">
          <p className="text-sm font-medium text-violet-300/90 uppercase tracking-wider">
            {label}
          </p>
          <p className="mt-2 text-3xl font-bold text-white">
            <AnimatedNumber value={value} format={format} unite={unite} />
          </p>
        </div>

        {icon && (
          <div className="p-3 rounded-full bg-violet-500/20 border border-violet-400/30 text-violet-200">
            {icon}
          </div>
        )}
      </div>

      {trend && (
        <div className={`mt-4 flex items-center pl-2 ${getTrendColor(trend, inverseTrend)}`}>
          <TrendIcon trend={trend} />
          <span className="ml-2 text-sm font-medium capitalize">
            {trend}
          </span>
        </div>
      )}
    </motion.div>
  );
};

export { AnimatedNumber };
export default KpiCard;
