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

  /**
   * Gestion de l'upload.
   */
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
    <div className="min-h-screen bg-gray-50 p-6">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">
          Upload de Données
        </h1>
        <p className="mt-2 text-gray-600">
          Importez vos fichiers CSV pour une analyse personnalisée
        </p>
      </div>

      {/* Instructions */}
      <div className="mb-8 bg-blue-50 rounded-xl p-6">
        <h2 className="text-lg font-semibold text-blue-900 mb-3">
          Formats acceptés
        </h2>
        <div className="grid md:grid-cols-3 gap-4">
          <div className="bg-white rounded-lg p-4">
            <h3 className="font-medium text-gray-900 mb-2">📊 Finance</h3>
            <p className="text-sm text-gray-600">
              Colonnes : date, revenue, cost, profit, growth_rate
            </p>
          </div>
          <div className="bg-white rounded-lg p-4">
            <h3 className="font-medium text-gray-900 mb-2">📈 Marketing</h3>
            <p className="text-sm text-gray-600">
              Colonnes : date, campaign_id, channel, budget, clicks, conversions
            </p>
          </div>
          <div className="bg-white rounded-lg p-4">
            <h3 className="font-medium text-gray-900 mb-2">🎧 Support</h3>
            <p className="text-sm text-gray-600">
              Colonnes : date, ticket_id, issue_type, resolution_hours, satisfaction_score
            </p>
          </div>
        </div>
      </div>

      {/* Zone d'upload */}
      <div className="bg-white rounded-xl shadow-md p-8">
        <FileUploader onUpload={handleUpload} isLoading={isUploading} />
      </div>

      {/* Erreur */}
      <AnimatePresence>
        {error && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            className="mt-6 p-4 bg-red-100 text-red-700 rounded-lg"
          >
            <div className="flex items-center gap-2">
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              {error}
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Résultat de l'upload */}
      <AnimatePresence>
        {uploadResults.length > 0 && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            className="mt-6 bg-white rounded-xl shadow-md p-6"
          >
            <div className="flex items-center gap-3 mb-4">
              <div className="p-2 bg-green-100 rounded-full">
                <svg className="w-6 h-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
              </div>
              <h3 className="text-lg font-semibold text-gray-900">
                Upload réussi ({uploadResults.length} fichier(s))
              </h3>
            </div>

            <div className="space-y-4">
              {uploadResults.map((uploadResult) => (
                <div key={uploadResult.filename} className="border border-gray-100 rounded-lg p-4">
                  <div className="grid md:grid-cols-2 gap-4">
                    <div>
                      <p className="text-sm text-gray-500">Fichier</p>
                      <p className="font-medium text-gray-900">{uploadResult.filename}</p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-500">Type détecté</p>
                      <p className="font-medium text-gray-900 capitalize">{uploadResult.file_type}</p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-500">Nombre de lignes</p>
                      <p className="font-medium text-gray-900">{uploadResult.row_count}</p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-500">Colonnes</p>
                      <p className="font-medium text-gray-900">{(uploadResult.columns || []).length}</p>
                    </div>
                  </div>

                  <div className="mt-4">
                    <p className="text-sm text-gray-500 mb-2">Colonnes détectées</p>
                    <div className="flex flex-wrap gap-2">
                      {(uploadResult.columns || []).map((col) => (
                        <span key={`${uploadResult.filename}-${col}`} className="px-3 py-1 bg-gray-100 rounded-full text-sm text-gray-700">
                          {col}
                        </span>
                      ))}
                    </div>
                  </div>

                  {uploadResult.validation_errors?.length > 0 && (
                    <div className="mt-4 p-3 bg-yellow-50 rounded-lg">
                      <p className="text-sm font-medium text-yellow-800 mb-1">Avertissements</p>
                      <ul className="text-sm text-yellow-700 list-disc list-inside">
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
