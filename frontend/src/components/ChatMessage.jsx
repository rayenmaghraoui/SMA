/**
 * ChatMessage — bulle de message (user/assistant).
 */

import { motion } from 'framer-motion';

/**
 * Avatar utilisateur.
 */
const UserAvatar = () => (
  <div className="w-10 h-10 rounded-full bg-blue-500 flex items-center justify-center text-white font-bold">
    U
  </div>
);

/**
 * Avatar assistant.
 */
const AssistantAvatar = () => (
  <div className="w-10 h-10 rounded-full bg-gradient-to-br from-purple-500 to-indigo-600 flex items-center justify-center">
    <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
    </svg>
  </div>
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
      {/* Avatar */}
      {isUser ? <UserAvatar /> : <AssistantAvatar />}

      {/* Bulle de message */}
      <div
        className={`max-w-[70%] rounded-2xl px-4 py-3 ${
          isUser
            ? 'bg-blue-500 text-white rounded-br-none'
            : isError
            ? 'bg-red-100 text-red-800 rounded-bl-none'
            : 'bg-gray-100 text-gray-800 rounded-bl-none'
        }`}
      >
        {/* Contenu */}
        <div className="whitespace-pre-wrap break-words">
          {content || (
            <span className="flex items-center gap-2">
              <span className="animate-pulse">En cours de rédaction</span>
              <span className="flex gap-1">
                <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
              </span>
            </span>
          )}
        </div>

        {/* Timestamp */}
        {timestamp && (
          <p className={`mt-1 text-xs ${isUser ? 'text-blue-100' : 'text-gray-400'}`}>
            {formatTime(timestamp)}
          </p>
        )}
      </div>
    </motion.div>
  );
};

export default ChatMessage;
