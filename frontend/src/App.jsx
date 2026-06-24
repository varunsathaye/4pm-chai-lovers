import React, { useState, useEffect } from 'react';
import InputForm from './components/InputForm';
import EmptyState from './components/EmptyState';
import LoadingState from './components/LoadingState';
import Header from './components/Dashboard/Header';
import KPIs from './components/Dashboard/KPIs';
import Charts from './components/Dashboard/Charts';
import DependencyTrace from './components/Dashboard/DependencyTrace';

const dummyResponse = {
  "pipeline_run": {
    "commit_hash": "a1b2c3d",
    "commit_message": "Refactor auth middleware and update user tests",
    "timestamp": "Just now",
    "status": "success"
  },
  "metrics": {
    "total_tests_in_suite": 45,
    "tests_executed": 4,
    "tests_skipped": 41,
    "standard_run_time_seconds": 210,
    "smart_run_time_seconds": 18,
    "time_saved_percentage": 91.4
  },
  "dependency_trace": [
    {
      "modified_file": "src/auth.py",
      "impacted_tests": [
        { "test_name": "test_login_success", "status": "passed", "duration_ms": 450 },
        { "test_name": "test_login_failure", "status": "passed", "duration_ms": 320 },
        { "test_name": "test_token_expiry", "status": "passed", "duration_ms": 500 },
        { "test_name": "test_role_permissions", "status": "passed", "duration_ms": 610 }
      ]
    }
  ]
};

export default function App() {
  const [repoUrl, setRepoUrl] = useState('');
  const [commitHash, setCommitHash] = useState('');
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [hasResults, setHasResults] = useState(false);
  const [pipelineData, setPipelineData] = useState(null);
  const [loadingStep, setLoadingStep] = useState(0);

  const loadingSteps = [
    "> Initialize connection...",
    "> Cloning repository...",
    "> Mapping Abstract Syntax Tree...",
    "> Selecting optimal tests...",
    "> Generating impact matrix..."
  ];

  const handleAnalyze = (e) => {
    e.preventDefault();
    if (!repoUrl.trim() || !commitHash.trim()) return;

    setIsAnalyzing(true);
    setHasResults(false);
    setPipelineData(null);
    setLoadingStep(0);

    setTimeout(() => {
      setPipelineData(dummyResponse);
      setHasResults(true);
      setIsAnalyzing(false);
    }, 2500);
  };

  useEffect(() => {
    let interval;
    if (isAnalyzing) {
      interval = setInterval(() => {
        setLoadingStep((prev) => (prev < loadingSteps.length - 1 ? prev + 1 : prev));
      }, 500);
    }
    return () => clearInterval(interval);
  }, [isAnalyzing]);

  return (
    <div className="min-h-screen bg-zinc-950 text-zinc-100 font-sans p-4 md:p-8 selection:bg-emerald-500/30">
      <div className="max-w-7xl mx-auto space-y-8">
        
        <InputForm 
          repoUrl={repoUrl} setRepoUrl={setRepoUrl}
          commitHash={commitHash} setCommitHash={setCommitHash}
          handleAnalyze={handleAnalyze} isAnalyzing={isAnalyzing}
        />

        {!hasResults && !isAnalyzing && <EmptyState />}
        
        {isAnalyzing && <LoadingState loadingSteps={loadingSteps} loadingStep={loadingStep} />}

        {hasResults && pipelineData && (
          <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-700">
            <Header pipeline_run={pipelineData.pipeline_run} />
            <KPIs metrics={pipelineData.metrics} />
            <Charts metrics={pipelineData.metrics} />
            <DependencyTrace dependency_trace={pipelineData.dependency_trace} />
          </div>
        )}
      </div>
    </div>
  );
}
