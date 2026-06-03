/**
 * ToastContainer — affiche les notifications en haut à droite.
 * À monter une seule fois dans App.jsx.
 */

import { useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { subscribeToast } from '../services/toast';

const ICONS = {
  success: (
    <svg className="w-4 h-4 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M5 13l4 4L19 7" />
    </svg>
  ),
  error: (
    <svg className="w-4 h-4 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M6 18L18 6M6 6l12 12" />
    </svg>
  ),
  warning: (
    <svg className="w-4 h-4 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z" />
    </svg>
  ),
  info: (
    <svg className="w-4 h-4 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
    </svg>
  ),
};

const STYLES = {
  success: 'bg-emerald-950/95 border-emerald-400/40 text-emerald-200 shadow-emerald-900/30',
  error:   'bg-rose-950/95 border-rose-400/40 text-rose-200 shadow-rose-900/30',
  warning: 'bg-amber-950/95 border-amber-400/40 text-amber-200 shadow-amber-900/30',
  info:    'bg-blue-950/95 border-blue-400/40 text-blue-200 shadow-blue-900/30',
};

const ToastContainer = () => {
  const [toasts, setToasts] = useState([]);

  const handleEvent = useCallback(({ id, message, type, action }) => {
    if (action === 'add') {
      setToasts(prev => [...prev, { id, message, type }]);
    } else {
      setToasts(prev => prev.filter(t => t.id !== id));
    }
  }, []);

  useEffect(() => subscribeToast(handleEvent), [handleEvent]);

  return (
    <div className="fixed top-20 right-4 z-[200] flex flex-col gap-2 pointer-events-none"
         style={{ maxWidth: '22rem', width: 'calc(100vw - 2rem)' }}>
      <AnimatePresence>
        {toasts.map(({ id, message, type }) => (
          <motion.div
            key={id}
            initial={{ opacity: 0, x: 60, scale: 0.92 }}
            animate={{ opacity: 1, x: 0,  scale: 1 }}
            exit={{   opacity: 0, x: 60,  scale: 0.92 }}
            transition={{ type: 'spring', stiffness: 340, damping: 28 }}
            className={`pointer-events-auto flex items-start gap-3 px-4 py-3
                        rounded-xl border shadow-xl backdrop-blur-sm
                        ${STYLES[type] || STYLES.info}`}
          >
            {ICONS[type] || ICONS.info}
            <p className="text-sm leading-relaxed flex-1">{message}</p>
          </motion.div>
        ))}
      </AnimatePresence>
    </div>
  );
};

export default ToastContainer;
