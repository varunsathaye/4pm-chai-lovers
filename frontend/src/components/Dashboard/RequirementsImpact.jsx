import React from 'react';
import { ShieldCheck, GitBranch, Gauge, Cpu } from 'lucide-react';

const ASIL_STYLES = {
  D: 'bg-rose-500/15 text-rose-300 border-rose-500/30',
  C: 'bg-orange-500/15 text-orange-300 border-orange-500/30',
  B: 'bg-amber-500/15 text-amber-300 border-amber-500/30',
  A: 'bg-sky-500/15 text-sky-300 border-sky-500/30',
  QM: 'bg-zinc-500/15 text-zinc-300 border-zinc-500/30',
};

const METHOD_LABELS = {
  coverage: { text: 'Coverage-based', cls: 'text-emerald-300 bg-emerald-500/10 border-emerald-500/30' },
  ast: { text: 'AST static', cls: 'text-sky-300 bg-sky-500/10 border-sky-500/30' },
  'full-fallback': { text: 'Safety fallback (full run)', cls: 'text-amber-300 bg-amber-500/10 border-amber-500/30' },
};

function asilClass(asil) {
  return ASIL_STYLES[asil] || ASIL_STYLES.QM;
}

export default function RequirementsImpact({ analysis, traceability, metrics }) {
  if (!analysis) return null;
  const method = METHOD_LABELS[analysis.selection_method] || METHOD_LABELS.coverage;
  const reqs = traceability?.impacted_requirements || [];
  const highestAsil = traceability?.highest_asil || 'QM';

  return (
    <div className="bg-zinc-900/50 rounded-2xl border border-zinc-800 overflow-hidden shadow-sm">
      <div className="p-5 md:p-6 border-b border-zinc-800/80 flex flex-wrap items-center gap-3">
        <h3 className="text-zinc-100 font-semibold flex items-center gap-2 text-lg">
          <ShieldCheck className="h-5 w-5 text-emerald-400" /> Requirements Impact & Selection
        </h3>
        <div className="flex flex-wrap gap-2 sm:ml-auto">
          <span className={`text-xs px-3 py-1.5 rounded-full border font-medium flex items-center gap-1.5 ${method.cls}`}>
            <Cpu className="h-3.5 w-3.5" /> {method.text}
          </span>
          <span className={`text-xs px-3 py-1.5 rounded-full border font-medium flex items-center gap-1.5 ${
            analysis.confidence === 'high'
              ? 'text-emerald-300 bg-emerald-500/10 border-emerald-500/30'
              : 'text-amber-300 bg-amber-500/10 border-amber-500/30'
          }`}>
            <Gauge className="h-3.5 w-3.5" /> {analysis.confidence} confidence
          </span>
        </div>
      </div>

      <div className="p-5 md:p-6 space-y-5">
        {/* Top strip: highest ASIL + expensive HIL tests avoided */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div className="bg-zinc-950/60 border border-zinc-800 rounded-xl p-4">
            <div className="text-[11px] uppercase tracking-wider text-zinc-500 font-bold mb-2">Highest ASIL touched</div>
            <span className={`text-sm px-3 py-1 rounded-md border font-bold ${asilClass(highestAsil)}`}>
              ASIL {highestAsil}
            </span>
          </div>
          <div className="bg-zinc-950/60 border border-zinc-800 rounded-xl p-4">
            <div className="text-[11px] uppercase tracking-wider text-zinc-500 font-bold mb-2">Expensive HIL tests avoided</div>
            <div className="text-2xl font-bold text-emerald-400">
              {metrics?.hil_tests_skipped ?? 0}
              <span className="text-sm text-zinc-500 font-normal"> / {metrics?.hil_tests_total ?? 0} HIL</span>
            </div>
          </div>
          <div className="bg-zinc-950/60 border border-zinc-800 rounded-xl p-4">
            <div className="text-[11px] uppercase tracking-wider text-zinc-500 font-bold mb-2">Changed source</div>
            <code className="text-xs text-indigo-300 font-mono break-all">
              {(analysis.modified_files || []).join(', ') || '—'}
            </code>
          </div>
        </div>

        {analysis.fallback_reason && (
          <div className="text-sm text-amber-300/90 bg-amber-500/10 border border-amber-500/30 rounded-xl px-4 py-3">
            <span className="font-semibold">Safety net engaged:</span> {analysis.fallback_reason} The full suite was run so no defect can slip through.
          </div>
        )}

        {/* Impacted requirements (ISO 26262 traceability) */}
        {reqs.length > 0 && (
          <div>
            <div className="text-[11px] uppercase tracking-wider text-zinc-500 font-bold mb-3 flex items-center gap-2">
              <GitBranch className="h-3.5 w-3.5" /> Impacted software requirements
            </div>
            <div className="space-y-2">
              {reqs.map((r) => (
                <div key={r.id} className="flex flex-col sm:flex-row sm:items-center gap-3 bg-zinc-950/60 border border-zinc-800 rounded-xl px-4 py-3">
                  <code className="text-sm text-indigo-300 font-mono font-semibold shrink-0">{r.id}</code>
                  <span className="text-sm text-zinc-300 flex-1">{r.title}</span>
                  <div className="flex items-center gap-2">
                    {r.component && (
                      <span className="text-[11px] text-zinc-400 bg-zinc-800/70 px-2.5 py-1 rounded-md">{r.component}</span>
                    )}
                    <span className={`text-[11px] px-2.5 py-1 rounded-md border font-bold ${asilClass(r.asil)}`}>ASIL {r.asil}</span>
                    <span className="text-[11px] text-zinc-500">{r.tests.length} test{r.tests.length !== 1 ? 's' : ''}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
