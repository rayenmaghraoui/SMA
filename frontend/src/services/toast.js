/**
 * Toast — système de notifications légères (singleton).
 * Pas de context React — utilisable partout (hooks, services).
 */

let _id = 0;
const _subscribers = new Set();

/**
 * Affiche un toast.
 * @param {string} message
 * @param {'success'|'error'|'warning'|'info'} type
 * @param {number} ms - durée d'affichage en ms
 */
export const showToast = (message, type = 'success', ms = 4000) => {
  const id = ++_id;
  _subscribers.forEach(fn => fn({ id, message, type, action: 'add' }));
  setTimeout(() => {
    _subscribers.forEach(fn => fn({ id, action: 'remove' }));
  }, ms);
};

/** Abonnement aux événements toast — retourne une fonction de désabonnement. */
export const subscribeToast = (fn) => {
  _subscribers.add(fn);
  return () => _subscribers.delete(fn);
};

export const toast = {
  success: (msg, ms) => showToast(msg, 'success', ms),
  error:   (msg, ms) => showToast(msg, 'error', ms),
  warning: (msg, ms) => showToast(msg, 'warning', ms),
  info:    (msg, ms) => showToast(msg, 'info', ms),
};
