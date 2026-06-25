import React, { useState, useRef, useEffect } from 'react';
import { LogOut, ChevronDown, User } from 'lucide-react';

const FALLBACK_AVATAR = 'data:image/svg+xml,' + encodeURIComponent(
  '<svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 100 100"><rect width="100" height="100" rx="50" fill="#27272a"/><text x="50" y="56" text-anchor="middle" fill="#a1a1aa" font-size="40" font-family="sans-serif" font-weight="600">G</text></svg>'
);

export default function ProfileMenu({ user, onLogout }) {
  const [open, setOpen] = useState(false);
  const ref = useRef(null);

  useEffect(() => {
    const handler = (e) => {
      if (ref.current && !ref.current.contains(e.target)) setOpen(false);
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, []);

  const avatarUrl = user?.avatar_url || FALLBACK_AVATAR;
  const displayName = user?.login || 'GitHub User';

  return (
    <div className="relative" ref={ref}>
      <button
        onClick={() => setOpen(!open)}
        className="flex items-center gap-2 bg-zinc-900/70 hover:bg-zinc-800/80 border border-zinc-800 rounded-full pl-1.5 pr-3 py-1 transition-all"
      >
        <img
          src={avatarUrl}
          alt=""
          className="w-8 h-8 rounded-full border border-zinc-700"
        />
        <span className="text-sm text-zinc-300 font-medium max-w-[100px] truncate hidden sm:inline">
          {displayName}
        </span>
        <ChevronDown className={`h-3.5 w-3.5 text-zinc-500 transition-transform ${open ? 'rotate-180' : ''}`} />
      </button>

      {open && (
        <div className="absolute right-0 mt-2 w-56 bg-zinc-900 border border-zinc-800 rounded-xl shadow-2xl shadow-black/50 overflow-hidden z-50">
          <div className="px-4 py-3 border-b border-zinc-800">
            <p className="text-sm font-medium text-zinc-200 truncate">{displayName}</p>
            <p className="text-xs text-zinc-500 truncate">{user?.login ? `@${user.login}` : ''}</p>
          </div>
          <button
            onClick={() => { onLogout(); setOpen(false); }}
            className="w-full flex items-center gap-3 px-4 py-3 text-sm text-zinc-400 hover:text-red-400 hover:bg-red-500/5 transition-colors"
          >
            <LogOut className="h-4 w-4" />
            Sign out
          </button>
        </div>
      )}
    </div>
  );
}
