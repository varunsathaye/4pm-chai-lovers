import React from 'react';
import GithubCallback from './GithubCallback'; // 1. IMPORT THIS

/**
 * GithubAuthGuard 
 * Acts as a layout wrapper and a mini-router. 
 */
export default function GithubAuthGuard({ isAuthenticated, setIsAuthenticated, onTokenReceived, children }) {
  const GITHUB_CLIENT_ID = import.meta.env.VITE_GITHUB_CLIENT_ID || 'YOUR_CLIENT_ID';
  const redirectUri = encodeURIComponent(`${window.location.origin}/auth/callback`);
  const githubAuthUrl = `https://github.com/login/oauth/authorize?client_id=${GITHUB_CLIENT_ID}&redirect_uri=${redirectUri}&scope=repo`;

  // 2. THE FIX: Intercept the URL path!
  // If GitHub just sent us back here, render the terminal handshake screen.
  if (window.location.pathname === '/auth/callback') {
    return <GithubCallback setIsAuthenticated={setIsAuthenticated} onTokenReceived={onTokenReceived} />;
  }

  // Render the protected dashboard if authenticated
  if (isAuthenticated) {
    return <>{children}</>;
  }

  // Render the OAuth prompt if unauthenticated
  return (
    <div className="min-h-screen bg-slate-950 font-sans flex flex-col items-center justify-center p-4 selection:bg-emerald-500/30">
      <div className="bg-slate-900/50 border border-slate-800 p-8 md:p-10 rounded-3xl max-w-md w-full text-center shadow-2xl backdrop-blur-xl">
        <div className="bg-slate-950 p-5 rounded-full inline-flex mb-8 border border-slate-800 shadow-inner">
          {/* GitHub Native SVG Logo */}
          <svg height="48" aria-hidden="true" viewBox="0 0 16 16" version="1.1" width="48" className="fill-slate-200">
            <path d="M8 0c4.42 0 8 3.58 8 8a8.013 8.013 0 0 1-5.45 7.59c-.4.08-.55-.17-.55-.38 0-.27.01-1.13.01-2.2 0-.75-.25-1.23-.54-1.48 1.78-.2 3.65-.88 3.65-3.95 0-.88-.31-1.59-.82-2.15.08-.2.36-1.02-.08-2.12 0 0-.67-.22-2.2.82-.64-.18-1.32-.27-2-.27-.68 0-1.36.09-2 .27-1.53-1.03-2.2-.82-2.2-.82-.44 1.1-.16 1.92-.08 2.12-.51.56-.82 1.28-.82 2.15 0 3.06 1.86 3.75 3.64 3.95-.23.2-.44.55-.51 1.07-.46.21-1.61.55-2.33-.66-.15-.24-.6-.83-1.23-.82-.67.01-.27.38.01.53.34.19.73.9.82 1.13.16.45.68 1.31 2.69.94 0 .67.01 1.3.01 1.49 0 .21-.15.45-.55.38A7.995 7.995 0 0 1 0 8c0-4.42 3.58-8 8-8Z"></path>
          </svg>
        </div>
        
        <h2 className="text-2xl md:text-3xl font-bold text-slate-50 mb-3 tracking-tight">Connect Repository</h2>
        <p className="text-slate-400 text-sm leading-relaxed mb-10">
          Authorize SmartTIA to read your Git history and codebase. We use this to map abstract syntax trees and compute execution routes instantly.
        </p>
        
        <a
          href={githubAuthUrl}
          className="w-full bg-emerald-600 hover:bg-emerald-500 text-white px-6 py-3.5 rounded-xl font-semibold transition-all shadow-[0_0_20px_-5px_theme(colors.emerald.500)] flex items-center justify-center gap-2"
        >
          Connect with GitHub
        </a>

        <button
          onClick={() => setIsAuthenticated(true)}
          className="mt-4 text-sm text-slate-400 hover:text-emerald-400 transition-colors font-medium"
        >
          Continue in demo mode &rarr;
        </button>

        <p className="mt-6 text-xs text-slate-600 font-medium uppercase tracking-wider">
          One-Shot Execution &bull; No Data Stored
        </p>
      </div>
    </div>
  );
}