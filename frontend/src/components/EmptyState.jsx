import React from 'react';
import { Search } from 'lucide-react';

export default function EmptyState() {
  return (
    <div className="flex flex-col items-center justify-center py-32 text-center">
      <div className="bg-zinc-900 border border-zinc-800 p-6 rounded-3xl mb-6 shadow-sm">
         <Search className="h-12 w-12 text-emerald-500/50" />
      </div>
      <h2 className="text-xl font-bold text-zinc-200 mb-2">Ready to Analyze Test Impact</h2>
      <p className="text-zinc-500 max-w-md">Enter your repository details and a target commit hash above to dynamically calculate optimal test execution routes.</p>
    </div>
  );
}