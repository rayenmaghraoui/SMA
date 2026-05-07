/**
 * ChatMessage — bulle de message (user/assistant).
 */

import { motion } from 'framer-motion';
import SqlResult from './SqlResult';

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
 * Transforme les segments inline (**gras**) en éléments React.
 */
const renderInline = (text, key) => {
  const parts = text.split(/(\*\*[^*]+\*\*)/g);
  return parts.map((part, i) => {
    if (part.startsWith('**') && part.endsWith('**')) {
      return <strong key={i} className="font-semibold text-white">{part.slice(2, -2)}</strong>;
    }
    return part;
  });
};

/**
 * Convertit du texte Markdown en JSX (headings, listes, gras).
 */
const renderMarkdown = (content) => {
  if (!content) return null;
  // Insère un saut de ligne avant chaque "Insight N:" et "Action N:" pour garantir
  // que chaque point est sur sa propre ligne, même si le LLM n'a pas mis de \n
  const normalized = content.replace(/(?<!\n)(Insight \d+:|Action \d+:)/g, '\n$1');
  const lines = normalized.split('\n');
  const elements = [];
  let i = 0;

  while (i < lines.length) {
    const line = lines[i];

    if (!line.trim()) { i++; continue; }

    if (line.startsWith('### ')) {
      elements.push(
        <h4 key={i} className="font-bold text-cyan-200 mt-3 mb-1 text-sm uppercase tracking-wide">
          {renderInline(line.slice(4))}
        </h4>
      );
      i++; continue;
    }
    if (line.startsWith('## ')) {
      elements.push(
        <h3 key={i} className="font-bold text-cyan-100 mt-4 mb-1 text-base">
          {renderInline(line.slice(3))}
        </h3>
      );
      i++; continue;
    }
    if (line.startsWith('# ')) {
      elements.push(
        <h2 key={i} className="font-bold text-white mt-4 mb-2 text-lg">
          {renderInline(line.slice(2))}
        </h2>
      );
      i++; continue;
    }

    // Liste à puces (* ou -)
    if (/^[*\-] /.test(line)) {
      const items = [];
      while (i < lines.length && /^[*\-] /.test(lines[i])) {
        items.push(
          <li key={i} className="flex gap-2">
            <span className="text-cyan-400 mt-0.5 flex-shrink-0">•</span>
            <span>{renderInline(lines[i].slice(2))}</span>
          </li>
        );
        i++;
      }
      elements.push(<ul key={`ul-${i}`} className="space-y-1 my-2">{items}</ul>);
      continue;
    }

    // Liste numérotée
    if (/^\d+\. /.test(line)) {
      const items = [];
      let num = 1;
      while (i < lines.length && /^\d+\. /.test(lines[i])) {
        const text = lines[i].replace(/^\d+\. /, '');
        items.push(
          <li key={i} className="flex gap-2">
            <span className="text-cyan-400 flex-shrink-0 font-mono">{num}.</span>
            <span>{renderInline(text)}</span>
          </li>
        );
        i++; num++;
      }
      elements.push(<ol key={`ol-${i}`} className="space-y-1 my-2">{items}</ol>);
      continue;
    }

    // Insight N: ou Action N: — chaque point sur sa propre ligne
    const insightMatch = line.match(/^(Insight \d+|Action \d+):\s*(.*)/);
    if (insightMatch) {
      const isAction = insightMatch[1].startsWith('Action');
      elements.push(
        <div key={i} className="flex gap-2 py-1">
          <span className={`flex-shrink-0 font-semibold text-sm ${isAction ? 'text-teal-300' : 'text-cyan-300'}`}>
            {insightMatch[1]}:
          </span>
          <span className="leading-relaxed">{renderInline(insightMatch[2])}</span>
        </div>
      );
      i++; continue;
    }

    elements.push(
      <p key={i} className="my-1 leading-relaxed">{renderInline(line)}</p>
    );
    i++;
  }

  return elements;
};

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
  const { role, content, timestamp, isError, sqlResult } = message;
  const isUser = role === 'user';

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className={`flex items-start gap-4 ${isUser ? 'flex-row-reverse' : ''}`}
    >
      {isUser ? <UserAvatar /> : <AssistantAvatar />}

      <div
        className={`max-w-[80%] rounded-2xl px-4 py-3 shadow-lg ${
          isUser
            ? 'bg-gradient-to-br from-cyan-400 to-teal-500 text-cyan-950 rounded-br-none border border-cyan-300/40'
            : isError
            ? 'bg-rose-500/25 text-rose-100 border border-rose-400/40 rounded-bl-none'
            : 'glass-panel-soft text-cyan-50 border-cyan-400/30 rounded-bl-none'
        }`}
      >
        <div className={isUser ? 'whitespace-pre-wrap break-words' : 'break-words'}>
          {isUser
            ? (content || null)
            : (content
                ? renderMarkdown(content)
                : (
                    <span className="flex items-center gap-2">
                      <span className="animate-pulse text-cyan-200">En cours de rédaction</span>
                      <span className="flex gap-1">
                        <span className="w-2 h-2 bg-cyan-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                        <span className="w-2 h-2 bg-cyan-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                        <span className="w-2 h-2 bg-cyan-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                      </span>
                    </span>
                  )
              )
          }
        </div>

        {/* Résultat SQL structuré */}
        {sqlResult && <SqlResult result={sqlResult} />}

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
