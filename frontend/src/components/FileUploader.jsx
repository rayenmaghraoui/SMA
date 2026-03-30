/**
 * FileUploader — drag-and-drop pour fichiers CSV.
 */

import { useState, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

/**
 * Composant FileUploader.
 */
const FileUploader = ({ onUpload, isLoading = false }) => {
  const [isDragging, setIsDragging] = useState(false);
  const [files, setFiles] = useState([]);
  const [error, setError] = useState('');

  /**
   * Vérifie que tous les fichiers sont des CSV.
   */
  const validateCsvFiles = useCallback((fileList) => {
    const selectedFiles = Array.from(fileList || []);

    if (selectedFiles.length === 0) {
      return { validFiles: [], errorMessage: '' };
    }

    const invalidFiles = selectedFiles.filter((currentFile) => !currentFile.name.endsWith('.csv'));

    if (invalidFiles.length > 0) {
      return {
        validFiles: [],
        errorMessage: 'Seuls les fichiers CSV sont acceptés.',
      };
    }

    return { validFiles: selectedFiles, errorMessage: '' };
  }, []);

  /**
   * Gestion du drag.
   */
  const handleDragOver = useCallback((e) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);

  /**
   * Gestion du drop.
   */
  const handleDrop = useCallback((e) => {
    e.preventDefault();
    setIsDragging(false);
    setError('');

    const { validFiles, errorMessage } = validateCsvFiles(e.dataTransfer.files);

    if (errorMessage) {
      setError(errorMessage);
      return;
    }

    setFiles(validFiles);
  }, [validateCsvFiles]);

  /**
   * Gestion du click pour sélection.
   */
  const handleFileSelect = useCallback((e) => {
    setError('');
    const { validFiles, errorMessage } = validateCsvFiles(e.target.files);

    if (errorMessage) {
      setError(errorMessage);
      return;
    }

    setFiles(validFiles);
  }, [validateCsvFiles]);

  /**
   * Upload du fichier.
   */
  const handleUpload = useCallback(async () => {
    if (files.length === 0 || !onUpload) return;

    try {
      await onUpload(files);
      setFiles([]);
    } catch (err) {
      setError(err.message || "Erreur lors de l'upload");
    }
  }, [files, onUpload]);

  /**
   * Supprimer le fichier sélectionné.
   */
  const handleRemove = useCallback(() => {
    setFiles([]);
    setError('');
  }, []);

  return (
    <div className="w-full">
      {/* Zone de drop */}
      <div
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        className={`relative border-2 border-dashed rounded-xl p-8 text-center transition-colors ${
          isDragging
            ? 'border-blue-500 bg-blue-50'
            : 'border-gray-300 hover:border-gray-400'
        }`}
      >
        <input
          type="file"
          accept=".csv"
          multiple
          onChange={handleFileSelect}
          className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
          disabled={isLoading}
        />

        <AnimatePresence mode="wait">
          {files.length > 0 ? (
            <motion.div
              key="file"
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.9 }}
              className="flex flex-col items-center"
            >
              <svg className="w-12 h-12 text-green-500 mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <p className="text-lg font-medium text-gray-900">
                {files.length} fichier(s) sélectionné(s)
              </p>
              <div className="mt-2 max-h-28 overflow-y-auto w-full">
                {files.map((currentFile) => (
                  <p key={`${currentFile.name}-${currentFile.lastModified}`} className="text-sm text-gray-500">
                    {currentFile.name} - {(currentFile.size / 1024).toFixed(1)} Ko
                  </p>
                ))}
              </div>
            </motion.div>
          ) : (
            <motion.div
              key="empty"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="flex flex-col items-center"
            >
              <svg className="w-12 h-12 text-gray-400 mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
              </svg>
              <p className="text-lg font-medium text-gray-900">
                Glissez votre fichier CSV ici
              </p>
              <p className="text-sm text-gray-500">
                ou cliquez pour sélectionner un ou plusieurs CSV
              </p>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Erreur */}
      {error && (
        <motion.p
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="mt-3 text-sm text-red-600"
        >
          {error}
        </motion.p>
      )}

      {/* Boutons */}
      {files.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="mt-4 flex justify-center gap-3"
        >
          <button
            onClick={handleRemove}
            className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors"
            disabled={isLoading}
          >
            Annuler
          </button>
          <button
            onClick={handleUpload}
            className="px-6 py-2 text-sm font-medium text-white bg-blue-500 rounded-lg hover:bg-blue-600 transition-colors disabled:opacity-50"
            disabled={isLoading}
          >
            {isLoading ? 'Upload en cours...' : 'Uploader'}
          </button>
        </motion.div>
      )}
    </div>
  );
};

export default FileUploader;
