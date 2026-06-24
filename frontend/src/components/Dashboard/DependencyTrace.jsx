import React from 'react';
import { FileCode2, LayoutDashboard, CheckCircle2, ServerCrash, Clock } from 'lucide-react';

export default function DependencyTrace({ dependency_trace }) {
  return (
    <div className="bg-zinc-900/50 rounded-2xl border border-zinc-800 overflow-hidden shadow-sm">
      <div className="p-6 border-b border-zinc-800/80 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <h3 className="text-zinc-100 font-semibold flex items-center gap-2 text-lg">
          <FileCode2 className="h-5 w-5 text-indigo-400" /> Dependency Trace & Executions
        </h3>
        <span className="bg-indigo-500/10 text-indigo-300 text-xs px-3.5 py-1.5 rounded-full border border-indigo-500/20 font-medium flex items-center gap-1.5">
          <LayoutDashboard className="h-3.5 w-3.5" /> Isolated Targets
        </span>
      </div>
      
      <div className="p-6 md:p-8">
        {dependency_trace.map((trace, idx) => (
          <div key={idx} className="mb-8 last:mb-0">
            <div className="flex flex-col sm:flex-row sm:items-center gap-4 mb-6 bg-zinc-800/40 p-4 md:p-5 rounded-xl border border-zinc-700/50">
               <div className="flex items-center justify-center p-3 bg-zinc-950/80 rounded-xl shadow-inner border border-zinc-800">
                  <LayoutDashboard className="h-6 w-6 text-indigo-400" />
               </div>
               <div>
                 <div className="text-[11px] text-zinc-500 font-bold uppercase tracking-wider w-full mb-1">Source Modified Node</div>
                 <code className="text-base text-indigo-300 font-mono tracking-tight">{trace.modified_file}</code>
               </div>
            </div>

            <div className="pl-6 md:pl-20 relative">
              <div className="absolute left-[34px] md:left-[90px] top-6 border-l-[2px] border-dashed border-zinc-700 h-[calc(100%-30px)] hidden sm:block"></div>
              <div className="space-y-3 relative z-10">
                <div className="text-[11px] text-zinc-500 font-bold uppercase tracking-wider mb-3 sm:ml-6 mt-1 flex items-center gap-2">
                   <CheckCircle2 className="h-3.5 w-3.5" /> Impacted Tests Validated
                </div>
                {trace.impacted_tests.map((test, tidx) => (
                  <div key={tidx} className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-4 md:px-6 rounded-xl bg-zinc-950 border border-zinc-800/80 sm:ml-6 group hover:border-zinc-600 transition-all hover:bg-zinc-900 relative">
                    <div className="hidden sm:block absolute -left-6 top-1/2 w-6 border-t-[2px] border-dashed border-zinc-700 pointer-events-none"></div>

                    <div className="flex items-center gap-3">
                      {test.status === 'passed' ? (
                        <CheckCircle2 className="h-5 w-5 text-emerald-500 drop-shadow-[0_0_8px_rgba(16,185,129,0.3)]" />
                      ) : (
                        <ServerCrash className="h-5 w-5 text-red-500" />
                      )}
                      <span className="text-[15px] font-mono text-zinc-300 group-hover:text-zinc-50 tracking-tight transition-colors">{test.test_name}</span>
                    </div>
                    <div className="flex items-center gap-4 text-sm">
                      <span className={`${test.status === 'passed' ? 'text-emerald-400 bg-emerald-500/10 border border-emerald-500/20' : 'text-red-400 bg-red-400/10 border border-red-500/30'} px-3 py-1 rounded-md capitalize font-semibold shadow-sm`}>
                        {test.status}
                      </span>
                      <span className="text-zinc-400 flex items-center gap-1.5 font-mono bg-zinc-900 border border-zinc-800 px-3 py-1 rounded-md">
                        <Clock className="h-3.5 w-3.5 text-zinc-500" />
                        {test.duration_ms}ms
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}