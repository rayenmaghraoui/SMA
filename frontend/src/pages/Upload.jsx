/**
 * Upload — page d'upload de fichiers CSV.
 */

import { useState, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import FileUploader from '../components/FileUploader';
import { uploadCSV } from '../services/uploadService';

/**
 * Page Upload.
 */
const Upload = () => {
  const [isUploading, setIsUploading] = useState(false);
  const [uploadResults, setUploadResults] = useState([]);
  const [error, setError] = useState('');

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

      if (failedUploads.length > 0) {
        setError(failedUploads.join(' | '));
      }
    } catch (err) {
      setError(err.response?.data?.detail || err.message || "Erreur lors de l'upload");
    } finally {
      setIsUploading(false);
    }
  }, []);

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
        <div className="grid md:grid-cols-3 gap-4">
          {[
            { icon: '📊', title: 'Finance', cols: 'Colonnes : date, revenue, cost, profit, growth_rate' },
            { icon: '📈', title: 'Marketing', cols: 'Colonnes : date, campaign_id, channel, budget, clicks, conversions' },
            { icon: '🎧', title: 'Support', cols: 'Colonnes : date, ticket_id, issue_type, resolution_hours, satisfaction_score' },
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
              <p className="text-sm text-cyan-200/85">{box.cols}</p>
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
