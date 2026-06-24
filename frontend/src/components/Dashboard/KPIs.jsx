import React from 'react';
import { FastForward, Clock, TestTube2 } from 'lucide-react';

export default function KPIs({ metrics }) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
      <div className="col-span-1 md:col-span-2 bg-gradient-to-br from-emerald-500/20 to-emerald-900/20 p-6 flex flex-col justify-center rounded-2xl border border-emerald-500/30 relative overflow-hidden shadow-lg shadow-emerald-500/5">
        <div className="absolute -top-10 -right-10 w-48 h-48 bg-emerald-500/20 blur-[60px] rounded-full pointer-events-none" />
        <div className="relative z-10 flex flex-col justify-center h-full">
          <h2 className="text-emerald-400 font-medium flex items-center gap-2 mb-2 uppercase tracking-wider text-sm">
            <FastForward className="h-4 w-4" /> Time Saved vs Standard
          </h2>
          <div className="flex items-baseline gap-2">
            <div className="text-6xl sm:text-7xl font-black text-white tracking-tight drop-shadow-sm">
              {metrics.time_saved_percentage}<span className="text-4xl sm:text-5xl text-emerald-400">%</span>
            </div>
          </div>
        </div>
      </div>

      <div className="bg-zinc-900/50 p-6 rounded-2xl border border-zinc-800 shadow-sm">
        <h3 className="text-zinc-400 text-sm font-medium mb-4 flex items-center gap-2 uppercase tracking-wider">
          <Clock className="h-4 w-4 text-indigo-400" /> Execution Time
        </h3>
        <div className="flex items-baseline gap-2 mb-1">
          <span className="text-4xl font-bold text-zinc-50">{metrics.smart_run_time_seconds}<span className="text-2xl text-zinc-500 font-normal">s</span></span>
        </div>
        <p className="text-sm text-zinc-500 mt-3 font-medium flex items-center gap-2">
          <span className="line-through decoration-red-500/50">{metrics.standard_run_time_seconds}s original duration</span>
        </p>
      </div>

      <div className="bg-zinc-900/50 p-6 rounded-2xl border border-zinc-800 shadow-sm">
        <h3 className="text-zinc-400 text-sm font-medium mb-4 flex items-center gap-2 uppercase tracking-wider">
          <TestTube2 className="h-4 w-4 text-cyan-400" /> Suite Efficiency
        </h3>
        <div className="flex items-baseline gap-2 mb-1">
          <span className="text-4xl font-bold text-emerald-400">{metrics.tests_executed}</span>
          <span className="text-zinc-500 font-medium whitespace-nowrap">/ {metrics.total_tests_in_suite} tests</span>
        </div>
        <p className="text-sm text-zinc-400 mt-3">
          <span className="text-zinc-300 font-semibold">{metrics.tests_skipped} test(s)</span> skipped safely
        </p>
      </div>
    </div>
  );
}