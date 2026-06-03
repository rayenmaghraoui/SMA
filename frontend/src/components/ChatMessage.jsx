/**
 * ChatMessage — bulle de message (user/assistant).
 */

import { motion } from 'framer-motion';
import SqlResult from './SqlResult';

/**
 * Avatar utilisateur — gradient cyan avec initiale.
 */
const UserAvatar = () => (
  <div className="w-10 h-10 rounded-full bg-gradient-to-br from-cyan-400 to-teal-500
                  flex items-center justify-center text-cyan-950 font-bold text-sm
                  shadow-md shadow-cyan-500/30 ring-2 ring-cyan-400/20 flex-shrink-0">
    U
  </div>
);

/**
 * Avatar assistant — gradient violet avec icône IA + point actif.
 */
const AssistantAvatar = () => (
  <div className="relative flex-shrink-0">
    <motion.div
      className="w-10 h-10 rounded-full bg-gradient-to-br from-violet-500 to-purple-700
                 flex items-center justify-center shadow-lg shadow-violet-500/40
                 ring-2 ring-violet-400/25"
      animate={{ scale: [1, 1.04, 1] }}
      transition={{ duration: 3, repeat: Infinity, ease: 'easeInOut' }}
    >
      {/* Icône étincelle / IA */}
      <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
          d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
      </svg>
    </motion.div>
    {/* Point vert "en ligne" */}
    <span className="absolute -bottom-0.5 -right-0.5 w-3 h-3 rounded-full bg-emerald-400 border-2 border-slate-900" />
  </div>
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
const ChatMessage = ({ message, onEdit, isStreaming = false }) => {
  const { role, content, timestamp, isError, sqlResult } = message;
  const isUser = role === 'user';

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className={`flex items-start gap-4 group ${isUser ? 'flex-row-reverse' : ''}`}
    >
      {isUser ? <UserAvatar /> : <AssistantAvatar />}

      <div className="flex flex-col gap-1 max-w-[80%]">
        <div
          className={`rounded-2xl px-4 py-3 shadow-lg ${
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
                  ? (
                    <>
                      {renderMarkdown(content)}
                      {/* Curseur clignotant pendant le streaming */}
                      {isStreaming && (
                        <motion.span
                          className="inline-block w-0.5 h-4 bg-violet-400 ml-0.5 align-middle"
                          animate={{ opacity: [1, 0, 1] }}
                          transition={{ duration: 0.75, repeat: Infinity }}
                        />
                      )}
                    </>
                  )
                  : (
                      <span className="flex items-center gap-2">
                        <span className="text-violet-300/80 text-sm italic">Rédaction en cours</span>
                        <motion.span
                          className="inline-block w-0.5 h-4 bg-violet-400 ml-1"
                          animate={{ opacity: [1, 0, 1] }}
                          transition={{ duration: 0.75, repeat: Infinity }}
                        />
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

        {/* Bouton édition — uniquement pour les messages user */}
        {isUser && onEdit && (
          <motion.button
            type="button"
            onClick={() => onEdit(message.id, content)}
            initial={{ opacity: 0 }}
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            className="self-end opacity-0 group-hover:opacity-100 flex items-center gap-1
                       text-xs text-cyan-400/70 hover:text-cyan-200 transition-all
                       px-2 py-1 rounded-lg hover:bg-cyan-500/15"
            title="Modifier ce message"
          >
            <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
            </svg>
            Modifier
          </motion.button>
        )}
      </div>
    </motion.div>
  );
};

export default ChatMessage;
