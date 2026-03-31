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

  const handleDragOver = useCallback((e) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);

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

  const handleFileSelect = useCallback((e) => {
    setError('');
    const { validFiles, errorMessage } = validateCsvFiles(e.target.files);

    if (errorMessage) {
      setError(errorMessage);
      return;
    }

    setFiles(validFiles);
  }, [validateCsvFiles]);

  const handleUpload = useCallback(async () => {
    if (files.length === 0 || !onUpload) return;

    try {
      await onUpload(files);
      setFiles([]);
    } catch (err) {
      setError(err.message || "Erreur lors de l'upload");
    }
  }, [files, onUpload]);

  const handleRemove = useCallback(() => {
    setFiles([]);
    setError('');
  }, []);

  return (
    <div className="w-full">
      <motion.div
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        animate={{
          borderColor: isDragging ? 'rgba(34, 211, 238, 0.8)' : 'rgba(34, 211, 238, 0.35)',
          backgroundColor: isDragging ? 'rgba(8, 145, 178, 0.25)' : 'rgba(8, 51, 68, 0.35)',
        }}
        className="relative border-2 border-dashed rounded-xl p-8 text-center transition-colors"
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
              <svg className="w-12 h-12 text-emerald-400 mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <p className="text-lg font-medium text-white">
                {files.length} fichier(s) sélectionné(s)
              </p>
              <div className="mt-2 max-h-28 overflow-y-auto w-full">
                {files.map((currentFile) => (
                  <p key={`${currentFile.name}-${currentFile.lastModified}`} className="text-sm text-cyan-200/85">
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
              <motion.svg
                className="w-12 h-12 text-cyan-400/80 mb-3"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
                animate={{ y: [0, -4, 0] }}
                transition={{ duration: 2, repeat: Infinity, ease: 'easeInOut' }}
              >
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
              </motion.svg>
              <p className="text-lg font-medium text-white">
                Glissez votre fichier CSV ici
              </p>
              <p className="text-sm text-cyan-200/80">
                ou cliquez pour sélectionner un ou plusieurs CSV
              </p>
            </motion.div>
          )}
        </AnimatePresence>
      </motion.div>

      {error && (
        <motion.p
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="mt-3 text-sm text-rose-300"
        >
          {error}
        </motion.p>
      )}

      {files.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="mt-4 flex justify-center gap-3"
        >
          <button
            type="button"
            onClick={handleRemove}
            className="px-4 py-2 text-sm font-medium text-cyan-100 bg-cyan-950/50 border border-cyan-400/30 rounded-lg hover:bg-cyan-500/20 transition-colors"
            disabled={isLoading}
          >
            Annuler
          </button>
          <motion.button
            type="button"
            onClick={handleUpload}
            className="px-6 py-2 text-sm font-medium text-cyan-950 bg-gradient-to-r from-cyan-300 to-teal-300 rounded-lg shadow-md shadow-cyan-900/25 disabled:opacity-50"
            disabled={isLoading}
            whileHover={{ scale: isLoading ? 1 : 1.03 }}
            whileTap={{ scale: isLoading ? 1 : 0.97 }}
          >
            {isLoading ? 'Upload en cours...' : 'Uploader'}
          </motion.button>
        </motion.div>
      )}
    </div>
  );
};

export default FileUploader;
