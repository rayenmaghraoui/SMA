/**
 * Service d'upload de fichiers CSV.
 */

import api from './api';

/**
 * Upload un fichier CSV pour analyse.
 *
 * @param {File} file - Fichier CSV à uploader
 * @returns {Promise<{
 *   success: boolean,
 *   filename: string,
 *   file_type: string,
 *   columns: string[],
 *   row_count: number,
 *   validation_errors: string[],
 *   message: string
 * }>}
 */
export const uploadCSV = async (file) => {
  const formData = new FormData();
  formData.append('file', file);

  const response = await api.post('/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });

  return response.data;
};

/**
 * Liste les fichiers uploadés disponibles.
 *
 * @returns {Promise<{files: Array, count: number}>}
 */
export const listUploads = async () => {
  const response = await api.get('/uploads');
  return response.data;
};

export default {
  uploadCSV,
  listUploads,
};
