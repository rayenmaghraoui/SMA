/**
 * ChatMessage — bulle de message (user/assistant).
 */

import { motion } from 'framer-motion';

/**
 * Avatar utilisateur.
 */
const UserAvatar = () => (
  <div className="w-10 h-10 rounded-full bg-gradient-to-br from-cyan-400 to-teal-500 flex items-center justify-center text-cyan-950 font-bold shadow-md shadow-cyan-500/30">
    U
  </div>
);

/**
 * Avatar assistant.
 */
const AssistantAvatar = () => (
  <motion.div
    className="w-10 h-10 rounded-full bg-gradient-to-br from-teal-400 to-cyan-600 flex items-center justify-center shadow-lg shadow-cyan-500/35"
    animate={{ scale: [1, 1.05, 1] }}
    transition={{ duration: 2.5, repeat: Infinity, ease: 'easeInOut' }}
  >
    <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
    </svg>
  </motion.div>
);

/**
 * Formate le timestamp.
 */
const formatTime = (date) => {
  if (!date) return '';
  const d = new Date(date);
  return d.toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' });
};

/**
 * Composant ChatMessage.
 */
const ChatMessage = ({ message }) => {
  const { role, content, timestamp, isError } = message;
  const isUser = role === 'user';

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className={`flex items-start gap-4 ${isUser ? 'flex-row-reverse' : ''}`}
    >
      {isUser ? <UserAvatar /> : <AssistantAvatar />}

      <div
        className={`max-w-[70%] rounded-2xl px-4 py-3 shadow-lg ${
          isUser
            ? 'bg-gradient-to-br from-cyan-400 to-teal-500 text-cyan-950 rounded-br-none border border-cyan-300/40'
            : isError
            ? 'bg-rose-500/25 text-rose-100 border border-rose-400/40 rounded-bl-none'
            : 'glass-panel-soft text-cyan-50 border-cyan-400/30 rounded-bl-none'
        }`}
      >
        <div className="whitespace-pre-wrap break-words">
          {content || (
            <span className="flex items-center gap-2">
              <span className="animate-pulse text-cyan-200">En cours de rédaction</span>
              <span className="flex gap-1">
                <span className="w-2 h-2 bg-cyan-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                <span className="w-2 h-2 bg-cyan-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                <span className="w-2 h-2 bg-cyan-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
              </span>
            </span>
          )}
        </div>

        {timestamp && (
          <p className={`mt-1 text-xs ${isUser ? 'text-cyan-900/70' : 'text-cyan-300/80'}`}>
            {formatTime(timestamp)}
          </p>
        )}
      </div>
    </motion.div>
  );
};

export default ChatMessage;
