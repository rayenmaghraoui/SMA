/**
 * KpiCard — carte d'affichage d'un KPI.
 */

import { motion } from 'framer-motion';

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
 * Détermine la couleur de tendance (lisible sur fond sombre).
 */
const getTrendColor = (trend, inverse = false) => {
  if (trend === 'hausse' || trend === 'up') {
    return inverse ? 'text-rose-400' : 'text-emerald-400';
  }
  if (trend === 'baisse' || trend === 'down') {
    return inverse ? 'text-emerald-400' : 'text-rose-400';
  }
  return 'text-cyan-300';
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
  className = '',
}) => {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      whileHover={{ y: -4, transition: { type: 'spring', stiffness: 400, damping: 25 } }}
      className={`glass-panel p-6 border-cyan-400/30 ${className}`}
    >
      <div className="flex items-center justify-between">
        <div className="flex-1">
          <p className="text-sm font-medium text-cyan-300/90 uppercase tracking-wider">
            {label}
          </p>
          <p className="mt-2 text-3xl font-bold text-white">
            {formatValue(value, format, unite)}
          </p>
        </div>

        {icon && (
          <div className="p-3 rounded-full bg-cyan-500/25 border border-cyan-400/35 text-cyan-200">
            {icon}
          </div>
        )}
      </div>

      {trend && (
        <div className={`mt-4 flex items-center ${getTrendColor(trend, inverseTrend)}`}>
          <TrendIcon trend={trend} />
          <span className="ml-2 text-sm font-medium capitalize">
            {trend}
          </span>
        </div>
      )}
    </motion.div>
  );
};

export default KpiCard;
