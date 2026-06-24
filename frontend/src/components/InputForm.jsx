import React from 'react';
import { GitCommit, Search } from 'lucide-react';

export default function InputForm({ repoUrl, setRepoUrl, commitHash, setCommitHash, handleAnalyze, isAnalyzing }) {
  return (
    <form onSubmit={handleAnalyze} className="bg-zinc-900/40 p-4 md:p-6 rounded-2xl border border-zinc-800 backdrop-blur-xl flex flex-col md:flex-row gap-4 items-end shadow-sm">
      <div className="w-full md:flex-1 space-y-2">
        <label className="text-xs font-semibold uppercase tracking-wider text-zinc-500 ml-1">Repository Path or URL</label>
        <div className="relative">
           <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
             <GitCommit className="h-4 w-4 text-zinc-500" />
           </div>
           <input 
             type="text" 
             required
             value={repoUrl}
             onChange={(e) => setRepoUrl(e.target.value)}
             className="w-full bg-zinc-950 border border-zinc-800 rounded-xl pl-10 pr-4 py-2.5 text-zinc-200 focus:outline-none focus:ring-2 focus:ring-emerald-500/50 focus:border-emerald-500/50 transition-all placeholder:text-zinc-700" 
             placeholder="e.g. /Users/dev/target-app or https://github..."
           />
        </div>
      </div>
      
      <div className="w-full md:w-64 space-y-2">
        <label className="text-xs font-semibold uppercase tracking-wider text-zinc-500 ml-1">Commit Hash</label>
        <input 
          type="text" 
          required
          value={commitHash}
          onChange={(e) => setCommitHash(e.target.value)}
          className="w-full bg-zinc-950 border border-zinc-800 rounded-xl px-4 py-2.5 text-zinc-200 focus:outline-none focus:ring-2 focus:ring-emerald-500/50 focus:border-emerald-500/50 transition-all placeholder:text-zinc-700" 
          placeholder="e.g. a1b2c3d"
        />
      </div>

      <button 
        type="submit" 
        disabled={isAnalyzing}
        className="w-full md:w-auto bg-emerald-600 hover:bg-emerald-500 text-white px-6 py-2.5 rounded-xl font-medium transition-all shadow-[0_0_20px_-5px_theme(colors.emerald.500)] disabled:opacity-50 disabled:shadow-none disabled:cursor-not-allowed flex items-center justify-center gap-2"
      >
        {isAnalyzing ? (
           <>
             <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
               <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
               <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
             </svg>
             Analyzing
           </>
        ) : (
           <>
             <Search className="h-4 w-4" /> 
             Analyze Impact
           </>
        )}
      </button>
    </form>
  );
}