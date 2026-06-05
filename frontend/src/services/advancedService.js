/**
 * Service d'analyse avancée — prévisions et comparaison de périodes.
 */

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

/**
 * Récupère la plage de dates disponible dans le dataset des ventes.
 *
 * @returns {Promise<{min_date: string, max_date: string}>}
 */
export const getDateRange = async () => {
  const res = await fetch(`${API_URL}/advanced/date-range`);
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
};

/**
 * Récupère la prévision des ventes pour les prochains mois.
 *
 * @param {number} horizon - Nombre de mois à prévoir (1-12)
 * @returns {Promise<Object>} { history, forecast, metadata }
 */
export const fetchForecast = async (horizon = 3) => {
  const res = await fetch(`${API_URL}/advanced/forecast`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ horizon }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `HTTP ${res.status}`);
  }
  return res.json();
};

/**
 * Compare deux périodes commerciales.
 *
 * @param {Object} periods - { period_a_start, period_a_end, period_b_start, period_b_end }
 * @returns {Promise<Object>} { period_a, period_b, evolution, category_comparison }
 */
export const comparePeriods = async (periods) => {
  const res = await fetch(`${API_URL}/advanced/compare`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(periods),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `HTTP ${res.status}`);
  }
  return res.json();
};

export default { getDateRange, fetchForecast, comparePeriods };
