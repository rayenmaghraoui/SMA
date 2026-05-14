/**
 * Upload — page d'upload de fichiers CSV.
 */

import { useState, useCallback, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import FileUploader from '../components/FileUploader';
import { uploadCSV, listUploads } from '../services/uploadService';

/**
 * Page Upload.
 */
const Upload = () => {
  const [isUploading, setIsUploading] = useState(false);
  const [uploadResults, setUploadResults] = useState([]);
  const [persistedUploads, setPersistedUploads] = useState([]);
  const [error, setError] = useState('');

  const loadPersistedUploads = useCallback(async () => {
    try {
      const response = await listUploads();
      setPersistedUploads(Array.isArray(response?.files) ? response.files : []);
    } catch (err) {
      console.warn('Impossible de charger la liste des uploads:', err);
    }
  }, []);

  useEffect(() => {
    loadPersistedUploads();
  }, [loadPersistedUploads]);

  const handleUpload = useCallback(async (files) => {
    setIsUploading(true);
    setError('');
    setUploadResults([]);

    try {
      const successfulResults = [];
      const failedUploads = [];

      for (const file of files) {
        try {
          const result = await uploadCSV(file);
          successfulResults.push({
            filename: result?.filename || file.name,
            file_type: result?.file_type || 'unknown',
            row_count: Number.isFinite(result?.row_count) ? result.row_count : 0,
            columns: Array.isArray(result?.columns) ? result.columns : [],
            validation_errors: Array.isArray(result?.validation_errors) ? result.validation_errors : [],
          });
        } catch (err) {
          const errorMessage = err.response?.data?.detail || err.message || "Erreur lors de l'upload";
          failedUploads.push(`${file.name}: ${errorMessage}`);
        }
      }

      setUploadResults(successfulResults);
      await loadPersistedUploads();

      if (failedUploads.length > 0) {
        setError(failedUploads.join(' | '));
      }
    } catch (err) {
      setError(err.response?.data?.detail || err.message || "Erreur lors de l'upload");
    } finally {
      setIsUploading(false);
    }
  }, [loadPersistedUploads]);

  const formatFileSize = (size) => {
    if (!Number.isFinite(size)) return '-';
    if (size < 1024) return `${size} o`;
    if (size < 1024 * 1024) return `${(size / 1024).toFixed(1)} Ko`;
    return `${(size / (1024 * 1024)).toFixed(2)} Mo`;
  };

  return (
    <div className="min-h-[calc(100vh-4rem)] p-6">
      <motion.div
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        className="mb-8"
      >
        <h1 className="text-3xl font-bold text-white drop-shadow-sm">
          Upload de Données
        </h1>
        <p className="mt-2 text-cyan-200/90">
          Importez vos fichiers CSV pour une analyse personnalisée
        </p>
      </motion.div>

      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.05 }}
        className="mb-8 glass-panel-soft p-6 border-cyan-400/30"
      >
        <h2 className="text-lg font-semibold text-cyan-100 mb-3">
          Formats acceptés
        </h2>
        <div className="grid md:grid-cols-3 lg:grid-cols-5 gap-4">
          {[
            { icon: '🛒', title: 'Ventes', cols: 'invoice_id, product_name, category, quantity, unit_price_tnd, revenue_tnd, customer_id, customer_region, sale_date, sales_channel, payment_method, estimated_profit' },
            { icon: '🗺️', title: 'Régions', cols: 'customer_region, CA_Total, Profit_Total, Nb_Transactions, Panier_Moyen' },
            { icon: '📦', title: 'Catégories', cols: 'category, CA_Total, Profit_Total, Nb_Transactions, Quantite_Vendue, Prix_Moyen' },
            { icon: '📡', title: 'Canaux', cols: 'sales_channel, CA_Total, Nb_Transactions, Panier_Moyen' },
            { icon: '📊', title: 'KPIs Globaux', cols: 'Indicateur, Valeur' },
          ].map((box, i) => (
            <motion.div
              key={box.title}
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.1 + i * 0.06 }}
              whileHover={{ y: -4 }}
              className="glass-panel p-4 border-cyan-300/20"
            >
              <h3 className="font-medium text-white mb-2">
                {box.icon} {box.title}
              </h3>
              <p className="text-xs text-cyan-200/85 leading-relaxed">{box.cols}</p>
            </motion.div>
          ))}
        </div>
      </motion.div>

      <motion.div
        initial={{ opacity: 0, scale: 0.99 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ delay: 0.12 }}
        className="glass-panel p-8"
      >
        <FileUploader onUpload={handleUpload} isLoading={isUploading} />
      </motion.div>

      <motion.div
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.16 }}
        className="mt-6 glass-panel p-6"
      >
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-lg font-semibold text-white">Fichiers uploadés persistés</h3>
          <button
            onClick={loadPersistedUploads}
            className="px-3 py-1.5 rounded-lg text-sm text-cyan-100 bg-cyan-500/20 border border-cyan-300/30 hover:bg-cyan-500/30"
            type="button"
          >
            Rafraîchir
          </button>
        </div>

        {persistedUploads.length === 0 ? (
          <p className="text-cyan-200/80 text-sm">Aucun fichier uploadé pour le moment.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-cyan-300/80 border-b border-cyan-400/20">
                  <th className="text-left py-2">Fichier</th>
                  <th className="text-left py-2">Taille</th>
                  <th className="text-left py-2">Dernière modification</th>
                </tr>
              </thead>
              <tbody>
                {persistedUploads.map((item) => (
                  <tr key={`${item.filename}-${item.modified}`} className="border-b border-cyan-400/10 text-cyan-100/95">
                    <td className="py-2 pr-3">{item.filename}</td>
                    <td className="py-2 pr-3">{formatFileSize(item.size)}</td>
                    <td className="py-2 pr-3">{item.modified ? new Date(item.modified * 1000).toLocaleString('fr-FR') : '-'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </motion.div>

      <AnimatePresence>
        {error && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            className="mt-6 p-4 rounded-xl bg-rose-500/20 border border-rose-400/35 text-rose-100"
          >
            <div className="flex items-center gap-2">
              <svg className="w-5 h-5 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              {error}
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      <AnimatePresence>
        {uploadResults.length > 0 && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            className="mt-6 glass-panel p-6"
          >
            <div className="flex items-center gap-3 mb-4">
              <div className="p-2 rounded-full bg-emerald-500/25 border border-emerald-400/40">
                <svg className="w-6 h-6 text-emerald-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
              </div>
              <h3 className="text-lg font-semibold text-white">
                Upload réussi ({uploadResults.length} fichier(s))
              </h3>
            </div>

            <div className="space-y-4">
              {uploadResults.map((uploadResult) => (
                <div key={uploadResult.filename} className="border border-cyan-400/20 rounded-xl p-4 bg-cyan-950/30">
                  <div className="grid md:grid-cols-2 gap-4">
                    <div>
                      <p className="text-sm text-cyan-300/80">Fichier</p>
                      <p className="font-medium text-white">{uploadResult.filename}</p>
                    </div>
                    <div>
                      <p className="text-sm text-cyan-300/80">Type détecté</p>
                      <p className="font-medium text-white capitalize">{uploadResult.file_type}</p>
                    </div>
                    <div>
                      <p className="text-sm text-cyan-300/80">Nombre de lignes</p>
                      <p className="font-medium text-white">{uploadResult.row_count}</p>
                    </div>
                    <div>
                      <p className="text-sm text-cyan-300/80">Colonnes</p>
                      <p className="font-medium text-white">{(uploadResult.columns || []).length}</p>
                    </div>
                  </div>

                  <div className="mt-4">
                    <p className="text-sm text-cyan-300/80 mb-2">Colonnes détectées</p>
                    <div className="flex flex-wrap gap-2">
                      {(uploadResult.columns || []).map((col) => (
                        <span key={`${uploadResult.filename}-${col}`} className="px-3 py-1 rounded-full text-sm text-cyan-100 bg-cyan-500/20 border border-cyan-400/25">
                          {col}
                        </span>
                      ))}
                    </div>
                  </div>

                  {uploadResult.validation_errors?.length > 0 && (
                    <div className="mt-4 p-3 rounded-lg bg-amber-500/15 border border-amber-400/30">
                      <p className="text-sm font-medium text-amber-200 mb-1">Avertissements</p>
                      <ul className="text-sm text-amber-100/90 list-disc list-inside">
                        {uploadResult.validation_errors.map((validationError, i) => (
                          <li key={`${uploadResult.filename}-warning-${i}`}>{validationError}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default Upload;
