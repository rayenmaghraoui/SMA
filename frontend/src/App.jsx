/**
 * App.jsx — composant racine avec routing.
 */

import { BrowserRouter, Routes, Route, NavLink, useLocation } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';

// Pages
import Dashboard from './pages/Dashboard';
import Upload from './pages/Upload';
import Chat from './pages/Chat';
import Report from './pages/Report';
import Advanced from './pages/Advanced';
import ParticleField3D from './components/ParticleField3D';
import ToastContainer from './components/ToastContainer';

/**
 * Navbar principale — verre violet animé.
 */
const Navbar = () => {
  const navItems = [
    { path: '/', label: 'Dashboard', icon: '📊' },
    { path: '/upload', label: 'Upload', icon: '📁' },
    { path: '/chat', label: 'Chat', icon: '💬' },
    { path: '/advanced', label: 'Analyse avancée', icon: '📈' },
    { path: '/report', label: 'Rapport', icon: '📋' },
  ];

  return (
    <motion.nav
      initial={{ y: -24, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      transition={{ type: 'spring', stiffness: 260, damping: 28 }}
      className="sticky top-0 z-50 border-b border-violet-500/15 bg-slate-950/80 backdrop-blur-xl shadow-lg shadow-slate-950/40"
    >
      <div className="max-w-7xl mx-auto px-4">
        <div className="flex items-center justify-between h-16">
          <motion.div
            className="flex items-center gap-3"
            whileHover={{ scale: 1.02 }}
            transition={{ type: 'spring', stiffness: 400, damping: 25 }}
          >
            <motion.div
              className="w-10 h-10 rounded-xl flex items-center justify-center bg-gradient-to-br from-violet-500 via-purple-500 to-violet-600 shadow-lg shadow-violet-500/40"
              animate={{ boxShadow: ['0 0 20px rgba(139, 92, 246, 0.35)', '0 0 32px rgba(168, 85, 247, 0.50)', '0 0 20px rgba(139, 92, 246, 0.35)'] }}
              transition={{ duration: 3, repeat: Infinity, ease: 'easeInOut' }}
            >
              <span className="text-white text-xl drop-shadow-md">🤖</span>
            </motion.div>
            <div>
              <h1 className="font-bold text-white tracking-tight">AI Business Consultant</h1>
              <p className="text-xs text-violet-200/90">Système Multi-Agents</p>
            </div>
          </motion.div>

          <div className="flex items-center gap-1">
            {navItems.map((item) => (
              <NavLink key={item.path} to={item.path} className="inline-flex rounded-lg">
                {({ isActive }) => (
                  <motion.span
                    className={`px-3 sm:px-4 py-2 rounded-lg font-medium flex items-center gap-2 relative overflow-hidden ${
                      isActive ? 'text-slate-900 shadow-md shadow-slate-900/25' : 'text-slate-100 hover:bg-violet-500/20 hover:text-white'
                    }`}
                    whileHover={{ scale: 1.04 }}
                    whileTap={{ scale: 0.98 }}
                  >
                    {isActive && (
                      <motion.span
                        layoutId="nav-pill"
                        className="absolute inset-0 bg-gradient-to-r from-violet-400 to-purple-400 rounded-lg -z-10"
                        transition={{ type: 'spring', stiffness: 380, damping: 30 }}
                      />
                    )}
                    <span className="relative z-10 flex items-center gap-2">
                      <span>{item.icon}</span>
                      <span className="hidden sm:inline">{item.label}</span>
                    </span>
                  </motion.span>
                )}
              </NavLink>
            ))}
          </div>
        </div>
      </div>
    </motion.nav>
  );
};

/**
 * Transition entre routes.
 */
const AnimatedRoutes = () => {
  const location = useLocation();

  return (
    <AnimatePresence mode="wait">
      <motion.div
        key={location.pathname}
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        exit={{ opacity: 0, y: -8 }}
        transition={{ duration: 0.28, ease: [0.22, 1, 0.36, 1] }}
      >
        <Routes location={location}>
          <Route path="/" element={<Dashboard />} />
          <Route path="/upload" element={<Upload />} />
          <Route path="/chat" element={<Chat />} />
          <Route path="/advanced" element={<Advanced />} />
          <Route path="/report" element={<Report />} />
        </Routes>
      </motion.div>
    </AnimatePresence>
  );
};

/**
 * Composant App principal.
 */
const App = () => {
  return (
    <BrowserRouter>
      <div className="relative min-h-screen text-slate-50 overflow-x-hidden">
        {/* Fond dégradé animé */}
        <div className="fixed inset-0 -z-20 app-shell-bg" aria-hidden />

        {/* Dot-grid pattern */}
        <div className="fixed inset-0 -z-10 dot-grid opacity-40 pointer-events-none" aria-hidden />

        {/* Champ de particules 3D — z=1 : au-dessus du fond (z=-10), sous le contenu (z=10) */}
        <div className="fixed inset-0 pointer-events-none" style={{ zIndex: 1 }} aria-hidden>
          <ParticleField3D />
        </div>

        {/* Orbes d'ambiance violet / purple / indigo */}
        <div className="fixed inset-0 -z-10 pointer-events-none overflow-hidden" aria-hidden>
          <motion.div
            className="absolute -top-40 -right-20 w-[420px] h-[420px] rounded-full bg-violet-500/20 blur-3xl"
            animate={{ scale: [1, 1.15, 1], opacity: [0.30, 0.50, 0.30] }}
            transition={{ duration: 8, repeat: Infinity, ease: 'easeInOut' }}
          />
          <motion.div
            className="absolute top-1/2 -left-32 w-[380px] h-[380px] rounded-full bg-purple-500/15 blur-3xl"
            animate={{ scale: [1.1, 1, 1.1], y: [0, 24, 0] }}
            transition={{ duration: 10, repeat: Infinity, ease: 'easeInOut' }}
          />
          <motion.div
            className="absolute bottom-0 right-1/4 w-[300px] h-[300px] rounded-full bg-indigo-400/15 blur-3xl"
            animate={{ opacity: [0.20, 0.40, 0.20] }}
            transition={{ duration: 6, repeat: Infinity, ease: 'easeInOut' }}
          />
        </div>

        <Navbar />
        <main className="relative z-10">
          <AnimatedRoutes />
        </main>
        <ToastContainer />
      </div>
    </BrowserRouter>
  );
};

export default App;
