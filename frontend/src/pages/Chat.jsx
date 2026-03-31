/**
 * Chat — interface de conversation avec l'assistant IA.
 */

import { useState, useRef, useEffect } from 'react';
import { motion } from 'framer-motion';
import ChatMessage from '../components/ChatMessage';
import AgentProgress from '../components/AgentProgress';
import useChat from '../hooks/useChat';

/**
 * Page Chat.
 */
const Chat = () => {
  const [input, setInput] = useState('');
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  const {
    messages,
    isLoading,
    currentStep,
    sendMessage,
    clearMessages,
  } = useChat();

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, currentStep]);

  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    sendMessage(input);
    setInput('');
  };

  const suggestions = [
    "Analysez les performances financières de l'entreprise",
    'Quels sont les canaux marketing les plus rentables ?',
    'Comment améliorer la satisfaction client ?',
    'Donnez-moi des recommandations pour augmenter la marge',
  ];

  return (
    <div className="min-h-[calc(100vh-4rem)] flex flex-col">
      <motion.div
        initial={{ opacity: 0, y: -8 }}
        animate={{ opacity: 1, y: 0 }}
        className="border-b border-cyan-400/25 bg-cyan-950/40 backdrop-blur-xl px-6 py-4"
      >
        <div className="flex items-center justify-between max-w-5xl mx-auto">
          <div>
            <h1 className="text-xl font-bold text-white">
              Assistant IA
            </h1>
            <p className="text-sm text-cyan-200/85">
              Posez vos questions sur les performances de votre entreprise
            </p>
          </div>
          {messages.length > 0 && (
            <motion.button
              type="button"
              onClick={clearMessages}
              className="text-sm text-cyan-200 hover:text-white px-3 py-1.5 rounded-lg hover:bg-cyan-500/25 transition-colors"
              whileHover={{ scale: 1.03 }}
              whileTap={{ scale: 0.97 }}
            >
              Nouvelle conversation
            </motion.button>
          )}
        </div>
      </motion.div>

      {isLoading && (
        <div className="border-b border-cyan-400/20 bg-cyan-950/35 backdrop-blur-md px-6 py-4">
          <div className="max-w-5xl mx-auto">
            <AgentProgress currentStep={currentStep} isLoading={isLoading} />
          </div>
        </div>
      )}

      <div className="flex-1 overflow-y-auto p-6">
        {messages.length === 0 ? (
          <div className="max-w-2xl mx-auto">
            <div className="text-center mb-8">
              <motion.div
                className="w-16 h-16 mx-auto mb-4 rounded-2xl flex items-center justify-center bg-gradient-to-br from-cyan-400 to-teal-500 shadow-lg shadow-cyan-500/35"
                animate={{ rotate: [0, 2, -2, 0] }}
                transition={{ duration: 4, repeat: Infinity, ease: 'easeInOut' }}
              >
                <svg className="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
                </svg>
              </motion.div>
              <h2 className="text-2xl font-bold text-white mb-2">
                Comment puis-je vous aider ?
              </h2>
              <p className="text-cyan-200/90">
                Je peux analyser vos données et vous fournir des recommandations personnalisées.
              </p>
            </div>

            <div className="grid gap-3">
              {suggestions.map((suggestion, index) => (
                <motion.button
                  key={index}
                  type="button"
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: index * 0.08 }}
                  whileHover={{ scale: 1.02, borderColor: 'rgba(34, 211, 238, 0.55)' }}
                  whileTap={{ scale: 0.99 }}
                  onClick={() => {
                    setInput(suggestion);
                    inputRef.current?.focus();
                  }}
                  className="p-4 text-left glass-panel-soft border border-cyan-400/25 hover:shadow-lg hover:shadow-cyan-500/10 transition-shadow"
                >
                  <p className="text-cyan-100">{suggestion}</p>
                </motion.button>
              ))}
            </div>
          </div>
        ) : (
          <div className="max-w-3xl mx-auto space-y-6">
            {messages.map((message) => (
              <ChatMessage key={message.id} message={message} />
            ))}
            <div ref={messagesEndRef} />
          </div>
        )}
      </div>

      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        className="border-t border-cyan-400/25 bg-cyan-950/45 backdrop-blur-xl p-4"
      >
        <form onSubmit={handleSubmit} className="max-w-3xl mx-auto">
          <div className="flex gap-3">
            <input
              ref={inputRef}
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Posez votre question..."
              disabled={isLoading}
              className="flex-1 px-4 py-3 rounded-xl border border-cyan-400/35 bg-cyan-950/50 text-white placeholder:text-cyan-400/60 focus:outline-none focus:ring-2 focus:ring-cyan-400/60 focus:border-transparent disabled:opacity-60"
            />
            <motion.button
              type="submit"
              disabled={isLoading || !input.trim()}
              className="px-6 py-3 rounded-xl font-medium text-cyan-950 bg-gradient-to-r from-cyan-300 to-teal-300 shadow-md shadow-cyan-900/30 disabled:opacity-50 disabled:cursor-not-allowed"
              whileHover={{ scale: isLoading || !input.trim() ? 1 : 1.05 }}
              whileTap={{ scale: isLoading || !input.trim() ? 1 : 0.96 }}
            >
              {isLoading ? (
                <svg className="w-5 h-5 animate-spin" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                </svg>
              ) : (
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
                </svg>
              )}
            </motion.button>
          </div>
        </form>
      </motion.div>
    </div>
  );
};

export default Chat;
