/**
 * Hook useChat — gestion de l'état du chat multi-conversations.
 *
 * Chaque conversation est stockée dans localStorage sous la clé
 * "sma_conversations". L'ID de la conversation active est stocké
 * sous "sma_active_conv".
 */

import { useState, useCallback, useRef, useEffect } from 'react';
import { streamChat, saveConversationsToServer, loadConversationsFromServer } from '../services/chatService';

const STORAGE_KEY = 'sma_conversations';
const ACTIVE_KEY  = 'sma_active_conv';
const MAX_MESSAGES = 100;

// ─── Utilitaires localStorage ────────────────────────────────────────────────

const genId    = () => `conv_${Date.now()}_${Math.random().toString(36).slice(2, 7)}`;
const genTitle = (msg) => {
  const clean = msg.trim().replace(/\s+/g, ' ');
  return clean.length > 45 ? clean.slice(0, 45) + '…' : clean;
};

const createEmptyConv = () => ({
  id: genId(),
  title: 'Nouvelle conversation',
  messages: [],
  createdAt: new Date().toISOString(),
  updatedAt: new Date().toISOString(),
});

const loadConversations = () => {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    return raw ? JSON.parse(raw) : [];
  } catch { return []; }
};

const loadActiveId = (convs) => {
  try {
    const id = localStorage.getItem(ACTIVE_KEY);
    return (id && convs.find((c) => c.id === id)) ? id : (convs[0]?.id || null);
  } catch { return convs[0]?.id || null; }
};

const persist = (convs, activeId) => {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(convs));
    if (activeId) localStorage.setItem(ACTIVE_KEY, activeId);
  } catch { /* localStorage plein — pas bloquant */ }
};

// ─── Dé-duplication LLM ──────────────────────────────────────────────────────

const dedupeAssistantContent = (content) => {
  if (!content || content.length < 200) return content;
  const normalized = content.replace(/\s+/g, ' ').trim();
  const half  = Math.floor(normalized.length / 2);
  const first = normalized.slice(0, half).trim();
  const second = normalized.slice(half).trim();
  if (first.length > 100 && (second.startsWith(first) || first === second)) return first;
  const anchor   = 'Analyse de la situation financière';
  const firstIdx = normalized.indexOf(anchor);
  if (firstIdx >= 0) {
    const secondIdx = normalized.indexOf(anchor, firstIdx + anchor.length + 20);
    if (secondIdx > 0) return normalized.slice(0, secondIdx).trim();
  }
  return normalized;
};

// ─── Export TXT ──────────────────────────────────────────────────────────────

const formatDateTime = (iso) => {
  if (!iso) return '';
  const d = new Date(iso);
  return d.toLocaleDateString('fr-FR', { day: '2-digit', month: '2-digit', year: 'numeric' })
    + ' à ' + d.toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
};

export const exportConversationsAsTxt = (conversations) => {
  const sep  = '═'.repeat(65);
  const dash = '─'.repeat(65);
  const now  = formatDateTime(new Date().toISOString());
  const lines = [];

  lines.push('='.repeat(65));
  lines.push('AI BUSINESS CONSULTANT — HISTORIQUE DES CONVERSATIONS');
  lines.push(`Exporté le : ${now}`);
  lines.push(`Nombre de conversations : ${conversations.length}`);
  lines.push('='.repeat(65));

  conversations.forEach((conv, idx) => {
    lines.push('');
    lines.push(sep);
    lines.push(`CONVERSATION ${idx + 1}/${conversations.length} — "${conv.title}"`);
    lines.push(`Créée le : ${formatDateTime(conv.createdAt)}`);
    lines.push(`Dernière activité : ${formatDateTime(conv.updatedAt)}`);
    lines.push(sep);

    if (!conv.messages || conv.messages.length === 0) {
      lines.push('(conversation vide)');
    } else {
      conv.messages.forEach((msg) => {
        lines.push('');
        const role = msg.role === 'user' ? 'VOUS' : 'ASSISTANT';
        lines.push(`[${role} — ${formatDateTime(msg.timestamp)}]`);
        lines.push(msg.content || '');
        lines.push(dash);
      });
    }
  });

  const blob = new Blob([lines.join('\n')], { type: 'text/plain;charset=utf-8' });
  const url  = URL.createObjectURL(blob);
  const a    = document.createElement('a');
  a.href     = url;
  a.download = `conversations_${new Date().toISOString().slice(0, 10)}.txt`;
  a.click();
  URL.revokeObjectURL(url);
};

// ─── Hook ─────────────────────────────────────────────────────────────────────

export const useChat = () => {
  const [conversations, setConversations] = useState(() => loadConversations());
  const [activeId, setActiveId] = useState(() => loadActiveId(loadConversations()));
  const [isLoading, setIsLoading]   = useState(false);
  const [currentStep, setCurrentStep] = useState('');
  const [report, setReport]         = useState(null);
  const cancelRef    = useRef(null);
  const isSendingRef = useRef(false);
  const saveTimerRef = useRef(null);
  // Ref pour capturer les messages courants sans les ajouter aux deps de sendMessage
  const messagesRef  = useRef([]);

  // Messages de la conversation active (dérivés)
  const activeConversation = conversations.find((c) => c.id === activeId) || null;
  const messages = activeConversation?.messages || [];

  // Synchronise le ref avec les messages courants
  messagesRef.current = messages;

  // Chargement initial depuis le backend (priorité sur localStorage)
  useEffect(() => {
    loadConversationsFromServer().then((serverConvs) => {
      if (serverConvs.length > 0) {
        setConversations(serverConvs);
        setActiveId((prev) => {
          const found = serverConvs.find((c) => c.id === prev);
          return found ? prev : (serverConvs[0]?.id || null);
        });
        persist(serverConvs, null);
      }
    });
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Sauvegarde localStorage + backend (debounced 2s, hors stream)
  useEffect(() => {
    if (!isLoading) {
      persist(conversations, activeId);
      clearTimeout(saveTimerRef.current);
      saveTimerRef.current = setTimeout(() => {
        saveConversationsToServer(conversations);
      }, 2000);
    }
  }, [conversations, activeId, isLoading]);

  // ── Créer une nouvelle conversation ──────────────────────────────────────
  const newConversation = useCallback(() => {
    const conv = createEmptyConv();
    setConversations((prev) => [conv, ...prev]);
    setActiveId(conv.id);
    setReport(null);
    setCurrentStep('');
    if (cancelRef.current) {
      cancelRef.current();
      setIsLoading(false);
      isSendingRef.current = false;
    }
  }, []);

  // ── Basculer vers une conversation existante ──────────────────────────────
  const switchConversation = useCallback((id) => {
    if (isLoading) return;
    setActiveId(id);
    setReport(null);
    setCurrentStep('');
  }, [isLoading]);

  // ── Supprimer une conversation ────────────────────────────────────────────
  const deleteConversation = useCallback((id) => {
    setConversations((prev) => {
      const updated = prev.filter((c) => c.id !== id);
      if (id === activeId) {
        setActiveId(updated[0]?.id || null);
      }
      return updated;
    });
  }, [activeId]);

  // ── Renommer une conversation ─────────────────────────────────────────────
  const renameConversation = useCallback((id, newTitle) => {
    const trimmed = newTitle.trim();
    if (!trimmed) return;
    setConversations((prev) =>
      prev.map((c) => c.id === id ? { ...c, title: trimmed } : c)
    );
  }, []);

  // ── Supprimer un message et tout ce qui suit (pour re-édition) ────────────
  const editMessageUpTo = useCallback((messageId) => {
    setConversations((prev) =>
      prev.map((c) => {
        if (c.id !== activeId) return c;
        const idx = c.messages.findIndex((m) => m.id === messageId);
        if (idx === -1) return c;
        return { ...c, messages: c.messages.slice(0, idx) };
      })
    );
  }, [activeId]);

  // ── Effacer les messages de la conversation active ────────────────────────
  const clearMessages = useCallback(() => {
    setConversations((prev) =>
      prev.map((c) =>
        c.id === activeId
          ? { ...c, messages: [], title: 'Nouvelle conversation', updatedAt: new Date().toISOString() }
          : c
      )
    );
    setReport(null);
    setCurrentStep('');
  }, [activeId]);

  // ── Envoyer un message ────────────────────────────────────────────────────
  const sendMessage = useCallback((message) => {
    if (!message.trim() || isLoading || isSendingRef.current) return;
    isSendingRef.current = true;

    // Si aucune conversation active, en créer une
    let targetId = activeId;
    if (!targetId) {
      const conv = createEmptyConv();
      setConversations((prev) => [conv, ...prev]);
      setActiveId(conv.id);
      targetId = conv.id;
    }

    const userMsg = {
      id: Date.now(),
      role: 'user',
      content: message,
      timestamp: new Date().toISOString(),
    };
    const assistantMsg = {
      id: Date.now() + 1,
      role: 'assistant',
      content: '',
      timestamp: new Date().toISOString(),
    };

    // Ajouter les messages + auto-titre si première question
    setConversations((prev) =>
      prev.map((c) => {
        if (c.id !== targetId) return c;
        const isFirst = c.messages.length === 0;
        return {
          ...c,
          title: isFirst ? genTitle(message) : c.title,
          messages: [...c.messages.slice(-(MAX_MESSAGES - 2)), userMsg, assistantMsg],
          updatedAt: new Date().toISOString(),
        };
      })
    );

    setIsLoading(true);
    setCurrentStep('Démarrage...');

    // Extraire les 3 derniers tours AVANT le nouveau message (6 msgs max)
    const history = messagesRef.current
      .slice(-6)
      .filter((m) => m.content && !m.isError)
      .map((m) => ({ role: m.role, content: m.content.slice(0, 500) }));

    cancelRef.current = streamChat(message, {
      onStep:  (step) => setCurrentStep(step),

      onToken: (token) => {
        setConversations((prev) =>
          prev.map((c) => {
            if (c.id !== targetId) return c;
            const msgs = [...c.messages];
            const last = msgs[msgs.length - 1];
            if (last?.role === 'assistant') {
              msgs[msgs.length - 1] = { ...last, content: last.content + token };
            }
            return { ...c, messages: msgs };
          })
        );
      },

      onSqlResult: (sqlResult) => {
        setConversations((prev) =>
          prev.map((c) => {
            if (c.id !== targetId) return c;
            const msgs = [...c.messages];
            const last = msgs[msgs.length - 1];
            if (last?.role === 'assistant') {
              msgs[msgs.length - 1] = { ...last, sqlResult, content: sqlResult.message || '' };
            }
            return { ...c, messages: msgs };
          })
        );
      },

      onReport: (newReport) => setReport(newReport),

      onDone: () => {
        setConversations((prev) =>
          prev.map((c) => {
            if (c.id !== targetId) return c;
            const msgs = [...c.messages];
            const last = msgs[msgs.length - 1];
            if (last?.role === 'assistant' && last.content) {
              msgs[msgs.length - 1] = { ...last, content: dedupeAssistantContent(last.content) };
            }
            return { ...c, messages: msgs, updatedAt: new Date().toISOString() };
          })
        );
        setIsLoading(false);
        setCurrentStep('');
        isSendingRef.current = false;
      },

      onError: (error) => {
        setConversations((prev) =>
          prev.map((c) => {
            if (c.id !== targetId) return c;
            const msgs = [...c.messages];
            const last = msgs[msgs.length - 1];
            if (last?.role === 'assistant') {
              msgs[msgs.length - 1] = { ...last, content: `Erreur: ${error}`, isError: true };
            }
            return { ...c, messages: msgs };
          })
        );
        setIsLoading(false);
        setCurrentStep('');
        isSendingRef.current = false;
      },
    }, history);
  }, [isLoading, activeId]);

  const cancelStream = useCallback(() => {
    if (cancelRef.current) {
      cancelRef.current();
      setIsLoading(false);
      setCurrentStep('');
      isSendingRef.current = false;
    }
  }, []);

  const exportTxt = useCallback(() => {
    exportConversationsAsTxt(conversations);
  }, [conversations]);

  return {
    messages,
    conversations,
    activeConversationId: activeId,
    isLoading,
    currentStep,
    report,
    sendMessage,
    cancelStream,
    clearMessages,
    newConversation,
    switchConversation,
    deleteConversation,
    renameConversation,
    editMessageUpTo,
    exportTxt,
  };
};

export default useChat;
