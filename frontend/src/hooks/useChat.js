/**
 * Hook useChat — gestion de l'état du chat.
 */

import { useState, useCallback, useRef } from 'react';
import { streamChat } from '../services/chatService';

/**
 * Supprime les duplications courantes de réponse LLM.
 * Cas visés: texte complet répété 2x à la suite.
 */
const dedupeAssistantContent = (content) => {
  if (!content || content.length < 200) return content;

  const normalized = content.replace(/\s+/g, ' ').trim();
  const half = Math.floor(normalized.length / 2);

  // Détection "A + A" (ou quasi identique) sur la réponse complète
  const first = normalized.slice(0, half).trim();
  const second = normalized.slice(half).trim();
  if (first.length > 100 && (second.startsWith(first) || first === second)) {
    return first;
  }

  // Détection via phrase d'ouverture répétée
  const anchor = 'Analyse de la situation financière';
  const firstIdx = normalized.indexOf(anchor);
  if (firstIdx >= 0) {
    const secondIdx = normalized.indexOf(anchor, firstIdx + anchor.length + 20);
    if (secondIdx > 0) {
      return normalized.slice(0, secondIdx).trim();
    }
  }

  return normalized;
};

/**
 * Hook pour gérer le chat avec streaming.
 *
 * @returns {{
 *   messages: Array,
 *   isLoading: boolean,
 *   currentStep: string,
 *   report: Object|null,
 *   sendMessage: function,
 *   clearMessages: function
 * }}
 */
export const useChat = () => {
  const [messages, setMessages] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [currentStep, setCurrentStep] = useState('');
  const [report, setReport] = useState(null);
  const cancelRef = useRef(null);
  const isSendingRef = useRef(false); // Protection contre double-envoi

  /**
   * Envoie un message et stream la réponse.
   * @param {string} message
   */
  const sendMessage = useCallback((message) => {
    // Protection contre double-envoi (StrictMode)
    if (!message.trim() || isLoading || isSendingRef.current) return;
    isSendingRef.current = true;

    // Ajouter le message utilisateur
    const userMessage = {
      id: Date.now(),
      role: 'user',
      content: message,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setIsLoading(true);
    setCurrentStep('Démarrage...');

    // Préparer le message assistant (vide au départ)
    const assistantMessage = {
      id: Date.now() + 1,
      role: 'assistant',
      content: '',
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, assistantMessage]);

    // Streamer la réponse
    cancelRef.current = streamChat(message, {
      onStep: (step) => {
        setCurrentStep(step);
      },

      onToken: (token) => {
        setMessages((prev) => {
          const updated = [...prev];
          const lastMessage = updated[updated.length - 1];
          if (lastMessage.role === 'assistant') {
            lastMessage.content += token;
          }
          return updated;
        });
      },

      onReport: (newReport) => {
        setReport(newReport);
      },

      onDone: () => {
        // Nettoyage final pour éviter l'affichage d'une réponse dupliquée
        setMessages((prev) => {
          const updated = [...prev];
          const lastMessage = updated[updated.length - 1];
          if (lastMessage?.role === 'assistant' && lastMessage.content) {
            lastMessage.content = dedupeAssistantContent(lastMessage.content);
          }
          return updated;
        });
        setIsLoading(false);
        setCurrentStep('');
        isSendingRef.current = false;
      },

      onError: (error) => {
        setMessages((prev) => {
          const updated = [...prev];
          const lastMessage = updated[updated.length - 1];
          if (lastMessage.role === 'assistant') {
            lastMessage.content = `Erreur: ${error}`;
            lastMessage.isError = true;
          }
          return updated;
        });
        setIsLoading(false);
        setCurrentStep('');
        isSendingRef.current = false;
      },
    });
  }, [isLoading]);

  /**
   * Annule le streaming en cours.
   */
  const cancelStream = useCallback(() => {
    if (cancelRef.current) {
      cancelRef.current();
      setIsLoading(false);
      setCurrentStep('');
    }
  }, []);

  /**
   * Efface tous les messages.
   */
  const clearMessages = useCallback(() => {
    setMessages([]);
    setReport(null);
    setCurrentStep('');
  }, []);

  return {
    messages,
    isLoading,
    currentStep,
    report,
    sendMessage,
    cancelStream,
    clearMessages,
  };
};

export default useChat;
