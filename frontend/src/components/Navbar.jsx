import React from 'react';
import { Zap } from 'lucide-react';
import ProfileMenu from './ProfileMenu';

export default function Navbar({ user, onLogout, isAuthenticated }) {
  if (!isAuthenticated) return null;

  return (
    <nav className="sticky top-0 z-50 w-full border-b border-zinc-800/60 bg-slate-950/80 backdrop-blur-xl">
      <div className=" mx-auto px-4 md:px-8">
        <div className="flex items-center justify-between h-16">
          <div className="flex items-center gap-3">
            <div className="flex items-center justify-center w-9 h-9 rounded-lg bg-gradient-to-br from-emerald-500 to-emerald-600 shadow-lg shadow-emerald-500/20">
              <Zap className="h-5 w-5 text-white" />
            </div>
            <div>
              <span className="text-lg font-bold text-white tracking-tight">SmartTIA</span>
              <span className="hidden sm:inline text-sm text-zinc-500 ml-2 font-medium">Test Impact Analysis</span>
            </div>
          </div>

          <div className="flex items-center gap-4">
            <ProfileMenu user={user} onLogout={onLogout} />
          </div>
        </div>
      </div>
    </nav>
  );
}
