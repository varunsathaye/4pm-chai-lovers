import React from 'react';
import { FileCode2, FolderGit2, Beaker, CheckCircle2, XCircle } from 'lucide-react';

export default function MapResults({ data }) {
  if (!data) return null;

  const { diff_summary, test_mapping, commit } = data;

  return (
    <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-700">
      {/* Header */}
      <div className="bg-zinc-900/50 rounded-2xl border border-zinc-800 p-6">
        <div className="flex items-center gap-3">
          <div className="p-3 bg-indigo-500/10 border border-indigo-500/20 rounded-xl">
            <FolderGit2 className="h-6 w-6 text-indigo-400" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-zinc-50">Static Impact Map</h1>
            <p className="text-sm text-zinc-400 mt-1">
              <span className="font-mono text-zinc-300">{commit.hash}</span>
              {commit.base && <span className="text-zinc-600"> (base: {commit.base})</span>}
            </p>
          </div>
        </div>
      </div>

      {/* Overview cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="bg-zinc-900/50 border border-zinc-800 rounded-xl p-5">
          <div className="text-[11px] uppercase tracking-wider text-zinc-500 font-bold mb-2">Source files changed</div>
          <div className="text-3xl font-bold text-indigo-300">{diff_summary.total_changed}</div>
        </div>
        <div className="bg-zinc-900/50 border border-zinc-800 rounded-xl p-5">
          <div className="text-[11px] uppercase tracking-wider text-zinc-500 font-bold mb-2">Functions impacted</div>
          <div className="text-3xl font-bold text-amber-300">{diff_summary.impacted_functions.length}</div>
        </div>
        <div className="bg-zinc-900/50 border border-zinc-800 rounded-xl p-5">
          <div className="text-[11px] uppercase tracking-wider text-zinc-500 font-bold mb-2">Test files impacted</div>
          <div className="text-3xl font-bold text-emerald-300">{test_mapping.total_impacted_test_files}</div>
        </div>
      </div>

      {/* Impacted functions */}
      <div className="bg-zinc-900/50 rounded-2xl border border-zinc-800 overflow-hidden">
        <div className="p-5 border-b border-zinc-800/80 flex items-center gap-2">
          <FileCode2 className="h-5 w-5 text-amber-400" />
          <h3 className="text-zinc-100 font-semibold">Changed Functions</h3>
        </div>
        <div className="p-5">
          {diff_summary.impacted_functions.length === 0 ? (
            <p className="text-sm text-zinc-500">No function-level changes detected.</p>
          ) : (
            <div className="space-y-2">
              {diff_summary.impacted_functions.map((fn, idx) => (
                <code key={idx} className="block text-sm font-mono text-amber-300/90 bg-amber-500/5 border border-amber-500/10 rounded-lg px-3 py-2">
                  {fn}
                </code>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Test mapping */}
      <div className="bg-zinc-900/50 rounded-2xl border border-zinc-800 overflow-hidden">
        <div className="p-5 border-b border-zinc-800/80 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Beaker className="h-5 w-5 text-emerald-400" />
            <h3 className="text-zinc-100 font-semibold">Impacted Test Files</h3>
          </div>
          <span className="text-xs text-zinc-500 bg-zinc-800/50 px-2.5 py-1 rounded-full">
            Must run: {test_mapping.total_impacted_test_files}
          </span>
        </div>
        <div className="p-5">
          {test_mapping.selected_test_files.length === 0 ? (
            <div className="flex items-center gap-3 text-sm text-amber-300/90 bg-amber-500/10 border border-amber-500/20 rounded-xl px-4 py-3">
              <XCircle className="h-5 w-5 shrink-0" />
              <span>No test files reference the changed functions. This could mean the change is untested, or the mapping couldn't find a connection.</span>
            </div>
          ) : (
            <div className="space-y-2">
              {test_mapping.selected_test_files.map((tf, idx) => (
                <div key={idx} className="flex items-center gap-3 bg-zinc-950 border border-zinc-800 rounded-xl px-4 py-3">
                  <CheckCircle2 className="h-4 w-4 text-emerald-500 shrink-0" />
                  <code className="text-sm font-mono text-zinc-300">{tf}</code>
                  <span className="text-[10px] text-emerald-400 ml-auto font-semibold uppercase">Selected</span>
                </div>
              ))}
            </div>
          )}

          {Object.keys(test_mapping.by_source).length > 0 && (
            <div className="mt-5">
              <div className="text-[11px] uppercase tracking-wider text-zinc-500 font-bold mb-3">Per-source breakdown</div>
              {Object.entries(test_mapping.by_source).map(([src, tests]) => (
                <div key={src} className="mb-3 last:mb-0">
                  <code className="text-xs text-indigo-300 font-mono">{src}</code>
                  <div className="mt-1 ml-4 space-y-1">
                    {tests.map((t, i) => (
                      <div key={i} className="flex items-center gap-2 text-sm text-zinc-400">
                        <span className="text-zinc-700">&#9492;</span> {t}
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
