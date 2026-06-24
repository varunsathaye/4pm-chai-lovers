import React, { useState, useEffect } from 'react';
import { Zap, ShieldAlert, AlertTriangle, CheckCircle2 } from 'lucide-react';
import InputForm from './components/InputForm';
import EmptyState from './components/EmptyState';
import LoadingState from './components/LoadingState';
import Header from './components/Dashboard/Header';
import KPIs from './components/Dashboard/KPIs';
import Charts from './components/Dashboard/Charts';
import DependencyTrace from './components/Dashboard/DependencyTrace';

import GithubAuthGuard from './components/GithubAuthGuard';

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000';

export default function App() {
  const [repoUrl, setRepoUrl] = useState('');
  const [commitHash, setCommitHash] = useState('');
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [hasResults, setHasResults] = useState(false);
  const [pipelineData, setPipelineData] = useState(null);
  const [loadingStep, setLoadingStep] = useState(0);
  const [error, setError] = useState(null);

  // Authentication State
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  const loadingSteps = [
    "> Cloning repository...",
    "> Parsing diff into Abstract Syntax Tree...",
    "> Mapping impacted source functions to tests...",
    "> Executing impacted subset on simulated HIL bench...",
    "> Measuring full-regression baseline & generating impact matrix..."
  ];

  useEffect(() => {
    let interval;
    if (isAnalyzing) {
      interval = setInterval(() => {
        setLoadingStep((prev) => (prev < loadingSteps.length - 1 ? prev + 1 : prev));
      }, 700);
    }
    return () => clearInterval(interval);
  }, [isAnalyzing]);

  const startRun = () => {
    setIsAnalyzing(true);
    setHasResults(false);
    setPipelineData(null);
    setError(null);
    setLoadingStep(0);
  };

  const finishRun = (data) => {
    setPipelineData(data);
    setHasResults(true);
    setIsAnalyzing(false);
  };

  const failRun = (message) => {
    setError(message);
    setIsAnalyzing(false);
  };

  const callApi = async (path, body) => {
    const res = await fetch(`${API_BASE}${path}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
    const payload = await res.json();
    if (!res.ok) throw new Error(payload.detail || `Server returned ${res.status}`);
    return payload;
  };

  const handleAnalyze = async (e) => {
    e.preventDefault();
    if (!repoUrl.trim() || !commitHash.trim()) return;
    startRun();
    try {
      const data = await callApi('/api/analyze', {
        repo_url: repoUrl.trim(),
        target_commit: commitHash.trim(),
      });
      finishRun(data);
    } catch (err) {
      failRun(err.message);
    }
  };

  const runDemo = async (scenario) => {
    startRun();
    try {
      const data = await callApi('/api/analyze/demo', { scenario });
      finishRun(data);
    } catch (err) {
      failRun(err.message);
    }
  };

  return (
    <GithubAuthGuard isAuthenticated={isAuthenticated} setIsAuthenticated={setIsAuthenticated}>
      <div className="min-h-screen bg-slate-950 text-slate-100 font-sans p-4 md:p-8 selection:bg-emerald-500/30">
        <div className="max-w-7xl mx-auto space-y-6">

          <InputForm
            repoUrl={repoUrl} setRepoUrl={setRepoUrl}
            commitHash={commitHash} setCommitHash={setCommitHash}
            handleAnalyze={handleAnalyze} isAnalyzing={isAnalyzing}
          />

          {/* Live demo bar -- runs against the bundled automotive ECU codebase */}
          <div className="flex flex-col sm:flex-row sm:items-center gap-3 bg-zinc-900/30 border border-zinc-800 rounded-2xl px-4 py-3">
            <span className="text-xs font-semibold uppercase tracking-wider text-zinc-500">
              Live demo · Automotive ECU suite
            </span>
            <div className="flex flex-wrap gap-3 sm:ml-auto">
              <button
                onClick={() => runDemo('safe')}
                disabled={isAnalyzing}
                className="flex items-center gap-2 bg-emerald-600/90 hover:bg-emerald-500 text-white text-sm px-4 py-2 rounded-xl font-medium transition-all disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <Zap className="h-4 w-4" /> Safe Refactor
              </button>
              <button
                onClick={() => runDemo('regression')}
                disabled={isAnalyzing}
                className="flex items-center gap-2 bg-rose-600/90 hover:bg-rose-500 text-white text-sm px-4 py-2 rounded-xl font-medium transition-all disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <ShieldAlert className="h-4 w-4" /> Inject Regression
              </button>
            </div>
          </div>

          {error && (
            <div className="flex items-start gap-3 bg-rose-500/10 border border-rose-500/30 text-rose-300 rounded-2xl px-5 py-4">
              <AlertTriangle className="h-5 w-5 mt-0.5 shrink-0" />
              <div>
                <div className="font-semibold">Analysis failed</div>
                <div className="text-sm text-rose-300/80 font-mono mt-1">{error}</div>
              </div>
            </div>
          )}

          {!hasResults && !isAnalyzing && !error && <EmptyState />}

          {isAnalyzing && <LoadingState loadingSteps={loadingSteps} loadingStep={loadingStep} />}

          {hasResults && pipelineData && (
            <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-700">
              {pipelineData.scenario && (
                <div className={`flex items-center gap-3 rounded-2xl px-5 py-4 border ${
                  pipelineData.analysis?.all_selected_passed
                    ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-300'
                    : 'bg-rose-500/10 border-rose-500/30 text-rose-300'
                }`}>
                  {pipelineData.analysis?.all_selected_passed
                    ? <CheckCircle2 className="h-5 w-5" />
                    : <ShieldAlert className="h-5 w-5" />}
                  <div className="text-sm">
                    <span className="font-semibold">{pipelineData.scenario.label}:</span>{' '}
                    {pipelineData.analysis?.all_selected_passed
                      ? 'Impacted tests re-selected and all passed — change is safe.'
                      : 'A regression was injected — and the selected subset CAUGHT it. No relevant test was skipped.'}
                  </div>
                </div>
              )}
              <Header pipeline_run={pipelineData.pipeline_run} />
              <KPIs metrics={pipelineData.metrics} />
              <Charts metrics={pipelineData.metrics} />
              <DependencyTrace dependency_trace={pipelineData.dependency_trace} />
            </div>
          )}
        </div>
      </div>
    </GithubAuthGuard>
  );
}
