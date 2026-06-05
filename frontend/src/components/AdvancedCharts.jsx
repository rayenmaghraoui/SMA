/**
 * AdvancedCharts — graphiques pour la page Analyse avancée.
 *
 *   - ForecastChart : historique + prévision avec bande de confiance.
 *   - CategoryComparisonChart : barres groupées CA par catégorie (période A vs B).
 */

import {
  ComposedChart,
  BarChart,
  Bar,
  Area,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';

const GRID_STROKE = 'rgba(139, 92, 246, 0.12)';
const AXIS_STROKE = '#c4b5fd';

/** Tooltip custom dans le thème violet. */
const VioletTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null;
  return (
    <div className="rounded-xl border border-violet-400/30 bg-slate-950/95 backdrop-blur-sm px-4 py-3 shadow-xl shadow-violet-900/30 text-sm">
      {label && <p className="text-violet-300 font-semibold mb-2">{label}</p>}
      {payload
        .filter((p) => p.value != null && p.dataKey !== 'range')
        .map((p) => (
          <div key={p.name} className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full flex-shrink-0" style={{ background: p.color }} />
            <span className="text-violet-200/80">{p.name}:</span>
            <span className="text-white font-medium">
              {typeof p.value === 'number'
                ? `${Math.round(p.value).toLocaleString('fr-FR')} TND`
                : p.value}
            </span>
          </div>
        ))}
    </div>
  );
};

/**
 * Graphique de prévision : historique (ligne pleine) + prévision (pointillés)
 * encadrée d'une bande de confiance.
 *
 * @param {Array} history  - [{ date, revenue }]
 * @param {Array} forecast - [{ date, revenue, lower, upper }]
 */
export const ForecastChart = ({ history = [], forecast = [] }) => {
  if (history.length === 0) {
    return (
      <div className="h-72 flex items-center justify-center text-violet-300/70">
        Aucune donnée disponible
      </div>
    );
  }

  // Dataset combiné : un point par mois.
  // Le dernier point historique amorce la ligne de prévision (jonction continue).
  const data = [
    ...history.map((h) => ({
      date: h.date,
      historique: h.revenue,
      prevision: null,
      range: null,
    })),
    ...forecast.map((f) => ({
      date: f.date,
      historique: null,
      prevision: f.revenue,
      range: [f.lower, f.upper],
    })),
  ];

  // Jonction : le dernier point historique sert d'ancrage à la courbe de prévision.
  if (history.length > 0 && forecast.length > 0) {
    const lastHist = history[history.length - 1];
    const joinIndex = history.length - 1;
    data[joinIndex] = { ...data[joinIndex], prevision: lastHist.revenue };
  }

  return (
    <ResponsiveContainer width="100%" height={340}>
      <ComposedChart data={data} margin={{ top: 20, right: 30, left: 10, bottom: 5 }}>
        <CartesianGrid strokeDasharray="3 3" stroke={GRID_STROKE} />
        <XAxis dataKey="date" stroke={AXIS_STROKE} fontSize={11} tick={{ fill: '#c4b5fd' }} />
        <YAxis
          stroke={AXIS_STROKE}
          fontSize={11}
          tick={{ fill: '#c4b5fd' }}
          tickFormatter={(v) => `${(v / 1000).toFixed(0)}k`}
        />
        <Tooltip content={<VioletTooltip />} />
        <Legend wrapperStyle={{ color: '#c4b5fd' }} />

        {/* Bande de confiance (intervalle [lower, upper]) */}
        <Area
          dataKey="range"
          name="Intervalle de confiance"
          stroke="none"
          fill="#a78bfa"
          fillOpacity={0.15}
          connectNulls
        />

        {/* Historique — ligne pleine cyan */}
        <Line
          type="monotone"
          dataKey="historique"
          name="Historique"
          stroke="#22d3ee"
          strokeWidth={2.5}
          dot={{ fill: '#22d3ee', r: 3 }}
          connectNulls
        />

        {/* Prévision — ligne pointillée violette */}
        <Line
          type="monotone"
          dataKey="prevision"
          name="Prévision"
          stroke="#c084fc"
          strokeWidth={2.5}
          strokeDasharray="6 4"
          dot={{ fill: '#c084fc', r: 3 }}
          connectNulls
        />
      </ComposedChart>
    </ResponsiveContainer>
  );
};

/**
 * Graphique de comparaison du CA par catégorie entre deux périodes.
 *
 * @param {Array}  data    - [{ category, period_a, period_b }]
 * @param {string} labelA  - Légende de la période A
 * @param {string} labelB  - Légende de la période B
 */
export const CategoryComparisonChart = ({ data = [], labelA = 'Période A', labelB = 'Période B' }) => {
  if (!data || data.length === 0) {
    return (
      <div className="h-72 flex items-center justify-center text-violet-300/70">
        Aucune donnée disponible
      </div>
    );
  }

  return (
    <ResponsiveContainer width="100%" height={340}>
      <BarChart data={data} margin={{ top: 20, right: 30, left: 10, bottom: 5 }}>
        <CartesianGrid strokeDasharray="3 3" stroke={GRID_STROKE} />
        <XAxis dataKey="category" stroke={AXIS_STROKE} fontSize={11} tick={{ fill: '#c4b5fd' }} />
        <YAxis
          stroke={AXIS_STROKE}
          fontSize={11}
          tick={{ fill: '#c4b5fd' }}
          tickFormatter={(v) => `${(v / 1000).toFixed(0)}k`}
        />
        <Tooltip content={<VioletTooltip />} cursor={{ fill: 'rgba(139,92,246,0.08)' }} />
        <Legend wrapperStyle={{ color: '#c4b5fd' }} />
        <Bar dataKey="period_a" name={labelA} fill="#22d3ee" radius={[4, 4, 0, 0]} />
        <Bar dataKey="period_b" name={labelB} fill="#c084fc" radius={[4, 4, 0, 0]} />
      </BarChart>
    </ResponsiveContainer>
  );
};

export default { ForecastChart, CategoryComparisonChart };
