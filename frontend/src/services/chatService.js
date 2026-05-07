/**
 * Service de chat avec streaming SSE.
 */

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

/**
 * Envoie un message et stream la réponse via SSE.
 *
 * @param {string} message - Message utilisateur
 * @param {Object} callbacks - Fonctions de callback
 * @param {function} callbacks.onStep      - Appelé pour chaque étape (step)
 * @param {function} callbacks.onToken     - Appelé pour chaque token
 * @param {function} callbacks.onReport    - Appelé avec le rapport final
 * @param {function} callbacks.onSqlResult - Appelé avec le résultat SQL {sql, rows_preview, chart_data, ...}
 * @param {function} callbacks.onDone      - Appelé à la fin
 * @param {function} callbacks.onError     - Appelé en cas d'erreur
 * @returns {function} Fonction pour annuler le stream
 */
export const streamChat = (message, callbacks) => {
  const { onStep, onToken, onReport, onSqlResult, onDone, onError } = callbacks;

  const controller = new AbortController();

  fetch(`${API_URL}/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message }),
    signal: controller.signal,
  })
    .then(async (response) => {
      if (!response.ok) throw new Error(`HTTP ${response.status}`);

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) { if (onDone) onDone(); break; }

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6));
              switch (data.type) {
                case 'step':
                  if (onStep) onStep(data.content);
                  break;
                case 'token':
                  if (onToken) onToken(data.content);
                  break;
                case 'report':
                  if (onReport) {
                    const report = typeof data.content === 'string'
                      ? JSON.parse(data.content)
                      : data.content;
                    onReport(report);
                  }
                  break;
                case 'sql_result':
                  if (onSqlResult) {
                    const result = typeof data.content === 'string'
                      ? JSON.parse(data.content)
                      : data.content;
                    onSqlResult(result);
                  }
                  break;
                case 'done':
                  if (onDone) onDone();
                  break;
                case 'error':
                  if (onError) onError(data.content);
                  break;
              }
            } catch (e) {
              console.warn('Erreur parsing SSE:', e, line);
            }
          }
        }
      }
    })
    .catch((error) => {
      if (error.name !== 'AbortError') {
        console.error('Erreur streaming:', error);
        if (onError) onError(error.message);
      }
    });

  return () => controller.abort();
};

/**
 * Version non-streaming du chat (pour les tests).
 *
 * @param {string} message - Message utilisateur
 * @returns {Promise<Object>}
 */
export const sendChatMessage = async (message) => {
  const response = await fetch(`${API_URL}/chat/simple`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ message }),
  });

  if (!response.ok) {
    throw new Error(`HTTP ${response.status}`);
  }

  return response.json();
};

export default {
  streamChat,
  sendChatMessage,
};
