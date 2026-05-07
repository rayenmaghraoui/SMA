/**
 * SqlResult — affiche le résultat d'une requête SQL générée par le LLM.
 *
 * Affiche :
 *   - La requête SQL générée (bloc de code)
 *   - Le tableau de résultats (100 premières lignes)
 *   - Un graphique Recharts selon le viz_type
 *   - Un bouton de téléchargement CSV
 */

import { useState } from 'react';
import { motion } from 'framer-motion';
import {
  BarChart, Bar, LineChart, Line, PieChart, Pie, Cell,
  ScatterChart, Scatter, XAxis, YAxis, CartesianGrid,
  Tooltip, Legend, ResponsiveContainer,
} from 'recharts';

// Palette de couleurs cohérente avec le thème cyan/teal
const COLORS = ['#22d3ee', '#2dd4bf', '#818cf8', '#f472b6', '#fb923c', '#a3e635'];

/**
 * Graphique Recharts adapté au viz_type.
 */
const SqlChart = ({ chartData }) => {
  if (!chartData || !chartData.data || chartData.data.length === 0) return null;

  const { x_key, y_keys, data } = chartData;

  // Déduire le type depuis le contexte parent via prop viz_type
  const type = chartData.viz_type || 'bar';

  if (type === 'pie') {
    const valueKey = y_keys[0];
    return (
      <ResponsiveContainer width="100%" height={280}>
        <PieChart>
          <Pie
            data={data}
            dataKey={valueKey}
            nameKey={x_key}
            cx="50%"
            cy="50%"
            outerRadius={100}
            label={({ name, percent }) => `${name} (${(percent * 100).toFixed(0)}%)`}
          >
            {data.map((_, i) => (
              <Cell key={i} fill={COLORS[i % COLORS.length]} />
            ))}
          </Pie>
          <Tooltip />
        </PieChart>
      </ResponsiveContainer>
    );
  }

  if (type === 'line') {
    return (
      <ResponsiveContainer width="100%" height={280}>
        <LineChart data={data} margin={{ top: 5, right: 20, left: 10, bottom: 60 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#164e63" />
          <XAxis dataKey={x_key} tick={{ fill: '#94a3b8', fontSize: 11 }} angle={-30} textAnchor="end" />
          <YAxis tick={{ fill: '#94a3b8', fontSize: 11 }} />
          <Tooltip contentStyle={{ background: '#0c1a2e', border: '1px solid #0e7490' }} />
          <Legend />
          {y_keys.map((key, i) => (
            <Line key={key} type="monotone" dataKey={key} stroke={COLORS[i % COLORS.length]} dot={false} />
          ))}
        </LineChart>
      </ResponsiveContainer>
    );
  }

  if (type === 'scatter' && y_keys.length >= 2) {
    return (
      <ResponsiveContainer width="100%" height={280}>
        <ScatterChart margin={{ top: 5, right: 20, left: 10, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#164e63" />
          <XAxis dataKey={y_keys[0]} name={y_keys[0]} tick={{ fill: '#94a3b8', fontSize: 11 }} />
          <YAxis dataKey={y_keys[1]} name={y_keys[1]} tick={{ fill: '#94a3b8', fontSize: 11 }} />
          <Tooltip contentStyle={{ background: '#0c1a2e', border: '1px solid #0e7490' }} cursor={{ strokeDasharray: '3 3' }} />
          <Scatter data={data} fill={COLORS[0]} />
        </ScatterChart>
      </ResponsiveContainer>
    );
  }

  // Bar chart par défaut
  return (
    <ResponsiveContainer width="100%" height={280}>
      <BarChart data={data} margin={{ top: 5, right: 20, left: 10, bottom: 60 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#164e63" />
        <XAxis dataKey={x_key} tick={{ fill: '#94a3b8', fontSize: 11 }} angle={-30} textAnchor="end" />
        <YAxis tick={{ fill: '#94a3b8', fontSize: 11 }} />
        <Tooltip contentStyle={{ background: '#0c1a2e', border: '1px solid #0e7490' }} />
        <Legend />
        {y_keys.map((key, i) => (
          <Bar key={key} dataKey={key} fill={COLORS[i % COLORS.length]} radius={[3, 3, 0, 0]} />
        ))}
      </BarChart>
    </ResponsiveContainer>
  );
};

/**
 * Composant principal SqlResult.
 *
 * @param {Object} props.result - Résultat SqlQueryResponse du backend
 */
const SqlResult = ({ result }) => {
  const [showSql, setShowSql] = useState(false);
  const [page, setPage] = useState(0);
  const PAGE_SIZE = 10;

  if (!result) return null;

  const { sql, rows_preview = [], total_rows = 0, chart_data, message } = result;
  const columns = rows_preview.length > 0 ? Object.keys(rows_preview[0]) : [];
  const totalPages = Math.ceil(rows_preview.length / PAGE_SIZE);
  const pageRows = rows_preview.slice(page * PAGE_SIZE, (page + 1) * PAGE_SIZE);

  // Export CSV côté client
  const handleDownloadCsv = () => {
    if (!rows_preview.length) return;
    const header = columns.join(',');
    const rowLines = rows_preview.map((row) =>
      columns.map((col) => {
        const val = row[col] ?? '';
        return typeof val === 'string' && val.includes(',') ? `"${val}"` : val;
      }).join(',')
    );
    const csv = [header, ...rowLines].join('\n');
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = 'resultats.csv';
    link.click();
    URL.revokeObjectURL(url);
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      className="mt-3 rounded-xl border border-cyan-500/30 bg-cyan-950/40 overflow-hidden"
    >
      {/* En-tête */}
      <div className="flex items-center justify-between px-4 py-2 bg-cyan-900/30 border-b border-cyan-500/20">
        <span className="text-sm font-semibold text-cyan-300">
          Résultat SQL · {total_rows} ligne{total_rows > 1 ? 's' : ''}
        </span>
        <div className="flex gap-2">
          {/* Bouton SQL */}
          <button
            onClick={() => setShowSql((v) => !v)}
            className="text-xs px-2 py-1 rounded-md bg-cyan-800/50 text-cyan-200 hover:bg-cyan-700/50 transition-colors"
          >
            {showSql ? 'Masquer SQL' : 'Voir SQL'}
          </button>
          {/* Bouton CSV */}
          {rows_preview.length > 0 && (
            <button
              onClick={handleDownloadCsv}
              className="text-xs px-2 py-1 rounded-md bg-teal-700/50 text-teal-200 hover:bg-teal-600/50 transition-colors"
            >
              ⬇ CSV
            </button>
          )}
        </div>
      </div>

      {/* Bloc SQL */}
      {showSql && sql && (
        <div className="px-4 py-3 bg-slate-900/60 border-b border-cyan-500/20">
          <pre className="text-xs text-cyan-100 overflow-x-auto whitespace-pre-wrap break-words">
            {sql}
          </pre>
        </div>
      )}

      {/* Graphique */}
      {chart_data && chart_data.data && chart_data.data.length > 0 && (
        <div className="px-4 pt-4 pb-2">
          <SqlChart chartData={chart_data} />
        </div>
      )}

      {/* Tableau */}
      {rows_preview.length > 0 && (
        <div className="overflow-x-auto">
          <table className="w-full text-xs text-left">
            <thead>
              <tr className="bg-cyan-900/40">
                {columns.map((col) => (
                  <th key={col} className="px-3 py-2 text-cyan-300 font-semibold whitespace-nowrap">
                    {col}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {pageRows.map((row, i) => (
                <tr
                  key={i}
                  className={i % 2 === 0 ? 'bg-cyan-950/20' : 'bg-cyan-900/10'}
                >
                  {columns.map((col) => (
                    <td key={col} className="px-3 py-1.5 text-slate-200 whitespace-nowrap">
                      {row[col] ?? '—'}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between px-4 py-2 border-t border-cyan-500/20 bg-cyan-950/20">
          <button
            disabled={page === 0}
            onClick={() => setPage((p) => p - 1)}
            className="text-xs px-3 py-1 rounded bg-cyan-800/50 text-cyan-200 disabled:opacity-40"
          >
            ← Préc.
          </button>
          <span className="text-xs text-slate-400">
            Page {page + 1} / {totalPages}
          </span>
          <button
            disabled={page === totalPages - 1}
            onClick={() => setPage((p) => p + 1)}
            className="text-xs px-3 py-1 rounded bg-cyan-800/50 text-cyan-200 disabled:opacity-40"
          >
            Suiv. →
          </button>
        </div>
      )}

      {rows_preview.length === 0 && (
        <p className="px-4 py-3 text-sm text-slate-400">{message || 'Aucun résultat.'}</p>
      )}
    </motion.div>
  );
};

export default SqlResult;
