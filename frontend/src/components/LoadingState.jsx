import React from 'react';
import { Terminal } from 'lucide-react';

export default function LoadingState({ loadingSteps, loadingStep }) {
  return (
    <div className="flex flex-col items-center justify-center py-24 px-4 w-full">
      <div className="bg-zinc-950 border border-zinc-800 rounded-2xl w-full max-w-2xl overflow-hidden shadow-2xl">
        <div className="bg-zinc-900 border-b border-zinc-800 px-4 py-3 flex items-center gap-2">
          <Terminal className="h-4 w-4 text-zinc-400" />
          <span className="text-xs text-zinc-500 font-mono">SmartTIA Engine v1.0</span>
        </div>
        <div className="p-6 font-mono text-sm space-y-3">
          {loadingSteps.map((step, idx) => (
             <div 
               key={idx} 
               className={`${idx <= loadingStep ? 'text-emerald-400' : 'text-zinc-800'} transition-colors duration-300`}
             >
               {step}
             </div>
          ))}
          <div className="text-zinc-500 animate-pulse">_</div>
        </div>
      </div>
    </div>
  );
}