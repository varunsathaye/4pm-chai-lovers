import React from 'react';
import { Zap, GitCommit, CheckCircle } from 'lucide-react';

export default function Header({ pipeline_run }) {
  return (
    <header className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-zinc-900/50 p-6 rounded-2xl border border-zinc-800 backdrop-blur-xl">
      <div className="flex items-center gap-4">
         <div className="p-3 bg-emerald-500/10 border border-emerald-500/20 rounded-xl relative shadow-[0_0_20px_-5px_theme(colors.emerald.500)]">
            <Zap className="h-6 w-6 text-emerald-400" />
         </div>
         <div>
           <h1 className="text-2xl font-bold text-zinc-50">Smart TIA Output</h1>
           <p className="text-zinc-400 text-sm flex items-center gap-2 mt-1">
             <GitCommit className="h-4 w-4" /> 
             <span className="font-mono text-zinc-300">{pipeline_run.commit_hash}</span> 
             &mdash; {pipeline_run.commit_message}
           </p>
         </div>
      </div>
      <div className="flex items-center gap-6 text-sm">
         <div className="text-right">
           <div className="text-zinc-400">Pipeline Status</div>
           <div className="flex items-center gap-1.5 justify-end mt-1">
             <CheckCircle className="h-4 w-4 text-emerald-400" />
             <span className="font-bold text-emerald-400 capitalize">{pipeline_run.status}</span>
           </div>
         </div>
         <div className="h-10 w-px bg-zinc-800 hidden md:block"></div>
         <div className="text-right hidden md:block">
           <div className="text-zinc-400">Timestamp</div>
           <div className="mt-1 text-zinc-300 font-medium">{pipeline_run.timestamp}</div>
         </div>
      </div>
    </header>
  );
}