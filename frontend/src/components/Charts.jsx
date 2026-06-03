/**
 * Charts — graphiques Recharts pour les KPIs (thème cyan sombre).
 */

import {
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
} from 'recharts';

const GRID_STROKE   = 'rgba(139, 92, 246, 0.12)';
const AXIS_STROKE   = '#c4b5fd';
const COLORS = ['#8b5cf6', '#a78bfa', '#7c3aed', '#c4b5fd', '#6d28d9', '#ddd6fe'];

/** Tooltip custom dans le thème violet */
const VioletTooltip = ({ active, payload, label, unit = 'TND' }) => {
  if (!active || !payload?.length) return null;
  return (
    <div className="rounded-xl border border-violet-400/30 bg-slate-950/95 backdrop-blur-sm px-4 py-3 shadow-xl shadow-violet-900/30 text-sm">
      {label && <p className="text-violet-300 font-semibold mb-2">{label}</p>}
      {payload.map((p) => (
        <div key={p.name} className="flex items-center gap-2">
          <span className="w-2 h-2 rounded-full flex-shrink-0" style={{ background: p.color }} />
          <span className="text-violet-200/80">{p.name}:</span>
          <span className="text-white font-medium">
            {typeof p.value === 'number'
              ? `${p.value.toLocaleString('fr-FR')} ${unit}`
              : p.value}
          </span>
        </div>
      ))}
    </div>
  );
};

/**
 * Graphique linéaire pour les revenus.
 */
export const RevenueChart = ({ data }) => {
  if (!data || data.length === 0) {
    return (
      <div className="h-64 flex items-center justify-center text-cyan-300/70">
        Aucune donnée disponible
      </div>
    );
  }

  return (
    <ResponsiveContainer width="100%" height={300}>
      <LineChart data={data} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
        <CartesianGrid strokeDasharray="3 3" stroke={GRID_STROKE} />
        <XAxis dataKey="date" stroke={AXIS_STROKE} fontSize={12} tick={{ fill: '#c4b5fd' }} />
        <YAxis stroke={AXIS_STROKE} fontSize={12} tick={{ fill: '#c4b5fd' }} tickFormatter={(v) => `${(v / 1000).toFixed(0)}k`} />
        <Tooltip content={<VioletTooltip />} />
        <Legend wrapperStyle={{ color: '#c4b5fd' }} />
        <Line
          type="monotone"
          dataKey="revenue"
          name="Chiffre d'affaires"
          stroke="#22d3ee"
          strokeWidth={2}
          dot={{ fill: '#22d3ee', strokeWidth: 2, r: 4 }}
          activeDot={{ r: 6 }}
        />
        <Line
          type="monotone"
          dataKey="profit"
          name="Bénéfice"
          stroke="#2dd4bf"
          strokeWidth={2}
          dot={{ fill: '#2dd4bf', strokeWidth: 2, r: 4 }}
        />
      </LineChart>
    </ResponsiveContainer>
  );
};

/**
 * Graphique en barres pour les canaux marketing.
 */
export const ChannelChart = ({ data }) => {
  if (!data || Object.keys(data).length === 0) {
    return (
      <div className="h-64 flex items-center justify-center text-cyan-300/70">
        Aucune donnée disponible
      </div>
    );
  }

  const chartData = Object.entries(data).map(([channel, roi]) => ({
    channel,
    roi: Number(roi) || 0,
  }));

  return (
    <ResponsiveContainer width="100%" height={300}>
      <BarChart data={chartData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
        <CartesianGrid strokeDasharray="3 3" stroke={GRID_STROKE} />
        <XAxis dataKey="channel" stroke={AXIS_STROKE} fontSize={12} tick={{ fill: '#c4b5fd' }} />
        <YAxis stroke={AXIS_STROKE} fontSize={12} tick={{ fill: '#c4b5fd' }} />
        <Tooltip content={<VioletTooltip />} />
        <Legend wrapperStyle={{ color: '#c4b5fd' }} />
        <Bar dataKey="roi" name="CA (TND)" radius={[4, 4, 0, 0]}>
          {chartData.map((entry, cellIndex) => (
            <Cell key={entry.channel} fill={COLORS[cellIndex % COLORS.length]} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
};

/**
 * Graphique circulaire pour la répartition.
 */
export const DistributionChart = ({ data, nameKey = 'name', valueKey = 'value' }) => {
  if (!data || data.length === 0) {
    return (
      <div className="h-64 flex items-center justify-center text-cyan-300/70">
        Aucune donnée disponible
      </div>
    );
  }

  return (
    <ResponsiveContainer width="100%" height={300}>
      <PieChart>
        <Pie
          data={data}
          cx="50%"
          cy="50%"
          innerRadius={60}
          outerRadius={100}
          paddingAngle={5}
          dataKey={valueKey}
          nameKey={nameKey}
          label={({ name, percent }) => `${name} (${(percent * 100).toFixed(0)}%)`}
        >
          {data.map((entry, cellIndex) => (
            <Cell key={entry[nameKey]} fill={COLORS[cellIndex % COLORS.length]} />
          ))}
        </Pie>
        <Tooltip content={<VioletTooltip unit="" />} />
        <Legend wrapperStyle={{ color: '#c4b5fd' }} />
      </PieChart>
    </ResponsiveContainer>
  );
};

/**
 * Graphique de satisfaction client.
 */
export const SatisfactionChart = ({ data }) => {
  if (!data || data.length === 0) {
    return (
      <div className="h-64 flex items-center justify-center text-cyan-300/70">
        Aucune donnée disponible
      </div>
    );
  }

  return (
    <ResponsiveContainer width="100%" height={300}>
      <LineChart data={data} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
        <CartesianGrid strokeDasharray="3 3" stroke={GRID_STROKE} />
        <XAxis dataKey="date" stroke={AXIS_STROKE} fontSize={12} tick={{ fill: '#c4b5fd' }} />
        <YAxis stroke={AXIS_STROKE} fontSize={12} domain={[0, 5]} ticks={[1, 2, 3, 4, 5]} tick={{ fill: '#c4b5fd' }} />
        <Tooltip content={<VioletTooltip unit="/5" />} />
        <Legend wrapperStyle={{ color: '#c4b5fd' }} />
        <Line
          type="monotone"
          dataKey="satisfaction"
          name="Score de satisfaction"
          stroke="#a78bfa"
          strokeWidth={2}
          dot={{ fill: '#a78bfa', strokeWidth: 2, r: 4 }}
        />
      </LineChart>
    </ResponsiveContainer>
  );
};

export default {
  RevenueChart,
  ChannelChart,
  DistributionChart,
  SatisfactionChart,
};
