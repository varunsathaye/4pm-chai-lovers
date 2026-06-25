import React, { useState, useEffect } from 'react';
import { ShieldAlert, AlertTriangle, CheckCircle2 } from 'lucide-react';
import InputForm from './components/InputForm';
import EmptyState from './components/EmptyState';
import LoadingState from './components/LoadingState';
import Header from './components/Dashboard/Header';
import KPIs from './components/Dashboard/KPIs';
import Charts from './components/Dashboard/Charts';
import DependencyTrace from './components/Dashboard/DependencyTrace';
import RequirementsImpact from './components/Dashboard/RequirementsImpact';
import MapResults from './components/Dashboard/MapResults';
import Navbar from './components/Navbar';

import GithubAuthGuard from './components/GithubAuthGuard';

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000';

const DEMO_COLORS = [
  { bg: 'bg-emerald-600/90 hover:bg-emerald-500' },
  { bg: 'bg-rose-600/90 hover:bg-rose-500' },
  { bg: 'bg-fuchsia-600/90 hover:bg-fuchsia-500' },
  { bg: 'bg-amber-600/90 hover:bg-amber-500' },
];

export default function App() {
  const [repoUrl, setRepoUrl] = useState('');
  const [commitHash, setCommitHash] = useState('');
  const [baseCommit, setBaseCommit] = useState('');
  const [sourceDir, setSourceDir] = useState('src/');
  const [testsDir, setTestsDir] = useState('tests');
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [hasResults, setHasResults] = useState(false);
  const [pipelineData, setPipelineData] = useState(null);
  const [mapData, setMapData] = useState(null);
  const [loadingStep, setLoadingStep] = useState(0);
  const [error, setError] = useState(null);

  // Authentication State
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [githubToken, setGithubToken] = useState(null);
  const [githubUser, setGithubUser] = useState(null);
  const [demoScenarios, setDemoScenarios] = useState(null);

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

  useEffect(() => {
    const savedToken = localStorage.getItem('github_token');
    const savedUser = localStorage.getItem('github_user');
    if (savedToken) {
      setGithubToken(savedToken);
      if (savedUser) {
        try { setGithubUser(JSON.parse(savedUser)); } catch { /* ignore */ }
      }
      setIsAuthenticated(true);
    }
  }, []);

  useEffect(() => {
    if (isAuthenticated) {
      const savedUser = localStorage.getItem('github_user');
      if (savedUser) {
        try { setGithubUser(JSON.parse(savedUser)); } catch { /* ignore */ }
      }
      fetch(`${API_BASE}/api/analyze/demo/scenarios`)
        .then(r => r.json())
        .then(data => setDemoScenarios(data))
        .catch(() => {});
    }
  }, [isAuthenticated]);

  const startRun = () => {
    setIsAnalyzing(true);
    setHasResults(false);
    setPipelineData(null);
    setMapData(null);
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
      const body = {
        repo_url: repoUrl.trim(),
        target_commit: commitHash.trim(),
        target_dir: sourceDir.trim() || 'src/',
        tests_dir: testsDir.trim() || 'tests',
      };
      if (baseCommit.trim()) {
        body.base_commit = baseCommit.trim();
      }
      if (githubToken) {
        body.github_token = githubToken;
      }
      const data = await callApi('/api/analyze', body);
      finishRun(data);
    } catch (err) {
      failRun(err.message);
    }
  };

  const handleQuickMap = async () => {
    if (!repoUrl.trim() || !commitHash.trim()) return;
    startRun();
    try {
      const body = {
        repo_url: repoUrl.trim(),
        target_commit: commitHash.trim(),
        source_dir: sourceDir.trim() || 'src/',
        tests_dir: testsDir.trim() || 'tests',
      };
      if (baseCommit.trim()) {
        body.base_commit = baseCommit.trim();
      }
      if (githubToken) {
        body.github_token = githubToken;
      }
      const data = await callApi('/api/analyze/map', body);
      setHasResults(true);
      setMapData(data);
      setIsAnalyzing(false);
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
    <GithubAuthGuard isAuthenticated={isAuthenticated} setIsAuthenticated={setIsAuthenticated} onTokenReceived={(token) => {
      setGithubToken(token);
      localStorage.setItem('github_token', token);
    }}>
      <div className="min-h-screen bg-slate-950 text-slate-100 font-sans selection:bg-emerald-500/30">
        <Navbar user={githubUser} isAuthenticated={isAuthenticated} onLogout={() => {
          localStorage.removeItem('github_token');
          localStorage.removeItem('github_user');
          setGithubToken(null);
          setGithubUser(null);
          setIsAuthenticated(false);
        }} />

        <div className="max-w-7xl mx-auto p-4 md:p-8 space-y-6">

          <InputForm
            repoUrl={repoUrl} setRepoUrl={setRepoUrl}
            commitHash={commitHash} setCommitHash={setCommitHash}
            baseCommit={baseCommit} setBaseCommit={setBaseCommit}
            sourceDir={sourceDir} setSourceDir={setSourceDir}
            testsDir={testsDir} setTestsDir={setTestsDir}
            handleAnalyze={handleAnalyze}
            handleQuickMap={handleQuickMap}
            isAnalyzing={isAnalyzing}
            githubToken={githubToken}
          />

          {/* Live demo bar -- runs against the bundled automotive ECU codebase */}
          {demoScenarios && (
            <div className="flex flex-col sm:flex-row sm:items-center gap-3 bg-zinc-900/30 border border-zinc-800 rounded-2xl px-4 py-3">
              <span className="text-xs font-semibold uppercase tracking-wider text-zinc-500">
                Live demo · Automotive ECU suite
              </span>
              <div className="flex flex-wrap gap-3 sm:ml-auto">
                {Object.entries(demoScenarios).map(([key, sc], idx) => (
                  <button
                    key={key}
                    onClick={() => runDemo(key)}
                    disabled={isAnalyzing}
                    className={`flex items-center gap-2 ${DEMO_COLORS[idx % DEMO_COLORS.length].bg} text-white text-sm px-4 py-2 rounded-xl font-medium transition-all disabled:opacity-50 disabled:cursor-not-allowed`}
                  >
                    {sc.label}
                  </button>
                ))}
              </div>
            </div>
          )}

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

          {hasResults && mapData && <MapResults data={mapData} />}

          {hasResults && pipelineData && (
            <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-700">
              {pipelineData.scenario && (
                <div className={`flex items-start gap-3 rounded-2xl px-5 py-4 border ${
                  pipelineData.analysis?.all_selected_passed
                    ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-300'
                    : 'bg-rose-500/10 border-rose-500/30 text-rose-300'
                }`}>
                  {pipelineData.analysis?.all_selected_passed
                    ? <CheckCircle2 className="h-5 w-5 mt-0.5 shrink-0" />
                    : <ShieldAlert className="h-5 w-5 mt-0.5 shrink-0" />}
                  <div className="text-sm">
                    <span className="font-semibold">{pipelineData.scenario.label}:</span>{' '}
                    {pipelineData.scenario.expectation}
                  </div>
                </div>
              )}
              <Header pipeline_run={pipelineData.pipeline_run} />
              <KPIs metrics={pipelineData.metrics} />
              <RequirementsImpact
                analysis={pipelineData.analysis}
                traceability={pipelineData.traceability}
                metrics={pipelineData.metrics}
              />
              <Charts metrics={pipelineData.metrics} />
              <DependencyTrace
                dependency_trace={pipelineData.dependency_trace}
                all_test_files={pipelineData.analysis?.all_test_files}
                selected_tests={pipelineData.analysis?.selected_tests}
              />
            </div>
          )}
        </div>
      </div>
    </GithubAuthGuard>
  );
}
