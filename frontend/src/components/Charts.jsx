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

const GRID_STROKE = 'rgba(34, 211, 238, 0.15)';
const AXIS_STROKE = '#a5f3fc';
const TOOLTIP_BG = 'rgba(8, 51, 68, 0.95)';
const TOOLTIP_BORDER = 'rgba(34, 211, 238, 0.35)';

const COLORS = ['#22d3ee', '#2dd4bf', '#38bdf8', '#fbbf24', '#fb7185', '#a78bfa'];

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
        <XAxis dataKey="date" stroke={AXIS_STROKE} fontSize={12} tick={{ fill: '#cffafe' }} />
        <YAxis stroke={AXIS_STROKE} fontSize={12} tick={{ fill: '#cffafe' }} tickFormatter={(v) => `${(v / 1000).toFixed(0)}k`} />
        <Tooltip
          contentStyle={{
            backgroundColor: TOOLTIP_BG,
            border: `1px solid ${TOOLTIP_BORDER}`,
            borderRadius: '8px',
            color: '#ecfeff',
          }}
          formatter={(value) => [`${value.toLocaleString()} TND`, 'Revenus']}
        />
        <Legend wrapperStyle={{ color: '#cffafe' }} />
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
        <XAxis dataKey="channel" stroke={AXIS_STROKE} fontSize={12} tick={{ fill: '#cffafe' }} />
        <YAxis stroke={AXIS_STROKE} fontSize={12} tick={{ fill: '#cffafe' }} />
        <Tooltip
          contentStyle={{
            backgroundColor: TOOLTIP_BG,
            border: `1px solid ${TOOLTIP_BORDER}`,
            borderRadius: '8px',
            color: '#ecfeff',
          }}
          formatter={(value) => [`${value.toFixed(1)}%`, 'ROI']}
        />
        <Legend wrapperStyle={{ color: '#cffafe' }} />
        <Bar dataKey="roi" name="ROI" radius={[4, 4, 0, 0]}>
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
        <Tooltip
          contentStyle={{
            backgroundColor: TOOLTIP_BG,
            border: `1px solid ${TOOLTIP_BORDER}`,
            borderRadius: '8px',
            color: '#ecfeff',
          }}
        />
        <Legend wrapperStyle={{ color: '#cffafe' }} />
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
        <XAxis dataKey="date" stroke={AXIS_STROKE} fontSize={12} tick={{ fill: '#cffafe' }} />
        <YAxis stroke={AXIS_STROKE} fontSize={12} domain={[0, 5]} ticks={[1, 2, 3, 4, 5]} tick={{ fill: '#cffafe' }} />
        <Tooltip
          contentStyle={{
            backgroundColor: TOOLTIP_BG,
            border: `1px solid ${TOOLTIP_BORDER}`,
            borderRadius: '8px',
            color: '#ecfeff',
          }}
          formatter={(value) => [`${value.toFixed(1)}/5`, 'Satisfaction']}
        />
        <Legend wrapperStyle={{ color: '#cffafe' }} />
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
