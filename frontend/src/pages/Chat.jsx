/**
 * Chat — interface de conversation avec l'assistant IA.
 * Layout : sidebar conversations (gauche) + zone de chat (droite).
 */

import { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import ChatMessage from '../components/ChatMessage';
import AgentProgress from '../components/AgentProgress';
import useChat from '../hooks/useChat';

/**
 * Formate une date en texte relatif (aujourd'hui, hier, date).
 */
const formatDate = (isoString) => {
  if (!isoString) return '';
  const d = new Date(isoString);
  const now = new Date();
  const diffDays = Math.floor((now - d) / 86_400_000);
  if (diffDays === 0) return d.toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' });
  if (diffDays === 1) return 'Hier';
  if (diffDays < 7) return d.toLocaleDateString('fr-FR', { weekday: 'short' });
  return d.toLocaleDateString('fr-FR', { day: '2-digit', month: 'short' });
};

/**
 * Sidebar — liste des conversations.
 */
const ConversationSidebar = ({
  conversations,
  activeConversationId,
  isLoading,
  onNew,
  onSwitch,
  onDelete,
  onRename,
  isOpen,
  onClose,
}) => {
  const [editingId, setEditingId] = useState(null);
  const [editingTitle, setEditingTitle] = useState('');
  const renameInputRef = useRef(null);

  const startRename = (e, conv) => {
    e.stopPropagation();
    setEditingId(conv.id);
    setEditingTitle(conv.title);
    setTimeout(() => renameInputRef.current?.select(), 30);
  };

  const commitRename = () => {
    if (editingId) onRename(editingId, editingTitle);
    setEditingId(null);
  };

  const handleRenameKey = (e) => {
    if (e.key === 'Enter') commitRename();
    if (e.key === 'Escape') setEditingId(null);
  };

  return (
  <>
    {/* Overlay mobile */}
    <AnimatePresence>
      {isOpen && (
        <motion.div
          key="overlay"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="fixed inset-0 z-20 bg-black/50 lg:hidden"
          onClick={onClose}
        />
      )}
    </AnimatePresence>

    {/* Sidebar */}
    <motion.aside
      initial={false}
      animate={{ x: isOpen ? 0 : '-100%' }}
      transition={{ type: 'spring', stiffness: 320, damping: 35 }}
      className="fixed top-16 left-0 bottom-0 z-30 w-72 flex flex-col
                 border-r border-cyan-400/20 bg-cyan-950/80 backdrop-blur-xl
                 lg:static lg:translate-x-0 lg:z-auto"
    >
      {/* Header sidebar */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-cyan-400/20">
        <span className="text-sm font-semibold text-cyan-100 tracking-wide">Conversations</span>
        <motion.button
          type="button"
          onClick={onNew}
          whileHover={{ scale: 1.08 }}
          whileTap={{ scale: 0.94 }}
          title="Nouvelle conversation"
          className="w-8 h-8 rounded-lg flex items-center justify-center
                     bg-cyan-500/20 hover:bg-cyan-500/40 text-cyan-300
                     hover:text-white transition-colors"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
          </svg>
        </motion.button>
      </div>

      {/* Liste des conversations */}
      <div className="flex-1 overflow-y-auto py-2 space-y-0.5 px-2">
        {conversations.length === 0 && (
          <p className="text-xs text-cyan-400/60 text-center mt-6">
            Aucune conversation
          </p>
        )}
        <AnimatePresence initial={false}>
          {conversations.map((conv) => {
            const isActive = conv.id === activeConversationId;
            const isEditing = editingId === conv.id;
            return (
              <motion.div
                key={conv.id}
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -10 }}
                className={`group flex items-center gap-2 rounded-lg px-3 py-2 cursor-pointer
                            transition-colors ${
                              isActive
                                ? 'bg-cyan-500/25 text-white'
                                : 'text-cyan-200/80 hover:bg-cyan-500/15 hover:text-white'
                            }`}
                onClick={() => { if (!isEditing) { onSwitch(conv.id); onClose(); } }}
              >
                {/* Icône */}
                <svg className="w-4 h-4 flex-shrink-0 opacity-70" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                    d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
                </svg>

                {/* Titre — input si en cours de renommage, sinon texte */}
                <div className="flex-1 min-w-0">
                  {isEditing ? (
                    <input
                      ref={renameInputRef}
                      type="text"
                      value={editingTitle}
                      onChange={(e) => setEditingTitle(e.target.value)}
                      onBlur={commitRename}
                      onKeyDown={handleRenameKey}
                      onClick={(e) => e.stopPropagation()}
                      className="w-full text-sm bg-cyan-900/60 border border-cyan-400/50
                                 rounded px-1 py-0.5 text-white outline-none focus:border-cyan-300"
                    />
                  ) : (
                    <>
                      <p className="text-sm truncate">{conv.title}</p>
                      <p className="text-xs text-cyan-400/60">{formatDate(conv.updatedAt)}</p>
                    </>
                  )}
                </div>

                {/* Actions : renommer + supprimer */}
                {!isEditing && (
                  <div className="opacity-0 group-hover:opacity-100 flex items-center gap-1 flex-shrink-0 transition-all">
                    <motion.button
                      type="button"
                      onClick={(e) => startRename(e, conv)}
                      whileHover={{ scale: 1.15 }}
                      whileTap={{ scale: 0.9 }}
                      title="Renommer"
                      className="w-6 h-6 flex items-center justify-center rounded
                                 text-cyan-400/70 hover:text-cyan-200"
                    >
                      <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                          d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                      </svg>
                    </motion.button>
                    <motion.button
                      type="button"
                      onClick={(e) => { e.stopPropagation(); onDelete(conv.id); }}
                      whileHover={{ scale: 1.15 }}
                      whileTap={{ scale: 0.9 }}
                      title="Supprimer"
                      className="w-6 h-6 flex items-center justify-center rounded
                                 text-cyan-400/70 hover:text-rose-400"
                    >
                      <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                          d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                      </svg>
                    </motion.button>
                  </div>
                )}
              </motion.div>
            );
          })}
        </AnimatePresence>
      </div>
    </motion.aside>
  </>
  );
};

/**
 * Page Chat.
 */
const Chat = () => {
  const [input, setInput] = useState('');
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  const {
    messages,
    conversations,
    activeConversationId,
    isLoading,
    currentStep,
    sendMessage,
    clearMessages,
    newConversation,
    switchConversation,
    deleteConversation,
    renameConversation,
    editMessageUpTo,
  } = useChat();

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, currentStep]);

  useEffect(() => {
    inputRef.current?.focus();
  }, [activeConversationId]);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;
    sendMessage(input);
    setInput('');
  };

  const handleEditMessage = (messageId, content) => {
    if (isLoading) return;
    editMessageUpTo(messageId);
    setInput(content);
    inputRef.current?.focus();
  };

  const suggestions = [
    { label: '📊 Stratégique', text: 'Comment améliorer la rentabilité par région ?' },
    { label: '📊 Stratégique', text: 'Quelles recommandations pour optimiser les canaux de vente ?' },
    { label: '📊 Stratégique', text: 'Analysez les tendances et donnez des recommandations stratégiques' },
    { label: '🔍 Données', text: 'Montre-moi le top 5 des produits par chiffre d\'affaires' },
    { label: '🔍 Données', text: 'Quelle région a le panier moyen le plus élevé ?' },
    { label: '🔍 Données', text: 'Compare les ventes par canal de vente' },
  ];

  return (
    <div className="flex h-[calc(100vh-4rem)] overflow-hidden">

      {/* ── Sidebar ── */}
      <ConversationSidebar
        conversations={conversations}
        activeConversationId={activeConversationId}
        isLoading={isLoading}
        onNew={newConversation}
        onSwitch={switchConversation}
        onDelete={deleteConversation}
        onRename={renameConversation}
        isOpen={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
      />

      {/* ── Zone principale ── */}
      <div className="flex-1 flex flex-col min-w-0">

        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -8 }}
          animate={{ opacity: 1, y: 0 }}
          className="border-b border-cyan-400/25 bg-cyan-950/40 backdrop-blur-xl px-4 py-3 flex-shrink-0"
        >
          <div className="flex items-center justify-between max-w-4xl mx-auto">
            <div className="flex items-center gap-3">
              {/* Toggle sidebar (mobile + desktop) */}
              <motion.button
                type="button"
                onClick={() => setSidebarOpen((v) => !v)}
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                className="lg:flex w-8 h-8 rounded-lg flex items-center justify-center
                           text-cyan-300 hover:bg-cyan-500/25 hover:text-white transition-colors"
                title="Conversations"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
                </svg>
              </motion.button>

              <div>
                <h1 className="text-base font-bold text-white truncate max-w-[200px] sm:max-w-xs">
                  {conversations.find((c) => c.id === activeConversationId)?.title || 'Assistant IA'}
                </h1>
                <p className="text-xs text-cyan-200/70">
                  {conversations.length} conversation{conversations.length !== 1 ? 's' : ''} sauvegardée{conversations.length !== 1 ? 's' : ''}
                </p>
              </div>
            </div>

            <div className="flex items-center gap-2">
              {messages.length > 0 && (
                <motion.button
                  type="button"
                  onClick={clearMessages}
                  className="text-xs text-cyan-300 hover:text-white px-3 py-1.5 rounded-lg
                             hover:bg-cyan-500/25 transition-colors border border-cyan-400/20"
                  whileHover={{ scale: 1.03 }}
                  whileTap={{ scale: 0.97 }}
                >
                  Effacer
                </motion.button>
              )}
              <motion.button
                type="button"
                onClick={newConversation}
                className="text-xs text-cyan-950 font-medium px-3 py-1.5 rounded-lg
                           bg-gradient-to-r from-cyan-300 to-teal-300 hover:opacity-90 transition-opacity"
                whileHover={{ scale: 1.03 }}
                whileTap={{ scale: 0.97 }}
              >
                + Nouveau
              </motion.button>
            </div>
          </div>
        </motion.div>

        {/* Barre de progression agent */}
        {isLoading && (
          <div className="border-b border-cyan-400/20 bg-cyan-950/35 backdrop-blur-md px-4 py-3 flex-shrink-0">
            <div className="max-w-4xl mx-auto">
              <AgentProgress currentStep={currentStep} isLoading={isLoading} />
            </div>
          </div>
        )}

        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-4 lg:p-6">
          {messages.length === 0 ? (
            <div className="max-w-2xl mx-auto">
              <div className="text-center mb-8">
                <motion.div
                  className="w-16 h-16 mx-auto mb-4 rounded-2xl flex items-center justify-center bg-gradient-to-br from-cyan-400 to-teal-500 shadow-lg shadow-cyan-500/35"
                  animate={{ rotate: [0, 2, -2, 0] }}
                  transition={{ duration: 4, repeat: Infinity, ease: 'easeInOut' }}
                >
                  <svg className="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                      d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
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
                    onClick={() => { setInput(suggestion.text); inputRef.current?.focus(); }}
                    className="p-4 text-left glass-panel-soft border border-cyan-400/25 hover:shadow-lg hover:shadow-cyan-500/10 transition-shadow"
                  >
                    <span className="text-xs font-medium text-cyan-400 mb-1 block">{suggestion.label}</span>
                    <p className="text-cyan-100">{suggestion.text}</p>
                  </motion.button>
                ))}
              </div>
            </div>
          ) : (
            <div className="max-w-3xl mx-auto space-y-6">
              {messages.map((message) => (
                <ChatMessage key={message.id} message={message} onEdit={handleEditMessage} />
              ))}
              <div ref={messagesEndRef} />
            </div>
          )}
        </div>

        {/* Input */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="border-t border-cyan-400/25 bg-cyan-950/45 backdrop-blur-xl p-4 flex-shrink-0"
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
                className="flex-1 px-4 py-3 rounded-xl border border-cyan-400/35
                           bg-cyan-950/50 text-white placeholder:text-cyan-400/60
                           focus:outline-none focus:ring-2 focus:ring-cyan-400/60
                           focus:border-transparent disabled:opacity-60"
              />
              <motion.button
                type="submit"
                disabled={isLoading || !input.trim()}
                className="px-6 py-3 rounded-xl font-medium text-cyan-950
                           bg-gradient-to-r from-cyan-300 to-teal-300
                           shadow-md shadow-cyan-900/30
                           disabled:opacity-50 disabled:cursor-not-allowed"
                whileHover={{ scale: isLoading || !input.trim() ? 1 : 1.05 }}
                whileTap={{ scale: isLoading || !input.trim() ? 1 : 0.96 }}
              >
                {isLoading ? (
                  <svg className="w-5 h-5 animate-spin" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor"
                      d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                  </svg>
                ) : (
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                      d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
                  </svg>
                )}
              </motion.button>
            </div>
          </form>
        </motion.div>
      </div>
    </div>
  );
};

export default Chat;
