import React from 'react';
import { motion } from 'framer-motion';
import {
  Activity,
  Code2,
  GitCommit,
  GitBranch,
  PlayCircle,
  Zap,
  CheckCircle2,
  Timer
} from 'lucide-react';
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer
} from 'recharts';

const mockData = [
  { commit: '1a2b3c', total: 120, run: 120, time: 450, smartTime: 450 },
  { commit: '4d5e6f', total: 121, run: 15, time: 460, smartTime: 45 },
  { commit: '7g8h9i', total: 121, run: 22, time: 455, smartTime: 65 },
  { commit: '0j1k2l', total: 125, run: 8, time: 480, smartTime: 25 },
  { commit: '3m4n5o', total: 125, run: 45, time: 475, smartTime: 120 },
];

function App() {
  return (
    <div className="min-h-screen bg-slate-950 text-slate-50 font-sans selection:bg-indigo-500/30">
      {/* Navigation */}
      <nav className="fixed w-full z-50 top-0 border-b border-white/5 bg-slate-950/50 backdrop-blur-md">
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-2 text-indigo-400 font-bold text-xl tracking-tight">
            <Activity className="h-6 w-6" />
            <span>SmartTIA</span>
          </div>
          <div className="hidden md:flex items-center gap-8 text-sm font-medium text-slate-300">
            <a href="#features" className="hover:text-white transition-colors">Features</a>
            <a href="#how-it-works" className="hover:text-white transition-colors">How it Works</a>
            <a href="#comparison" className="hover:text-white transition-colors">Metrics</a>
          </div>
          <button className="bg-indigo-600 hover:bg-indigo-500 text-white px-5 py-2 rounded-full text-sm font-medium transition-all shadow-[0_0_20px_-5px_theme(colors.indigo.500)]">
            View Dashboard
          </button>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="relative pt-32 pb-20 lg:pt-48 lg:pb-32 overflow-hidden mx-6">
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[800px] bg-indigo-500/20 rounded-full blur-[120px] pointer-events-none" />
        
        <div className="relative max-w-5xl mx-auto text-center space-y-8">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
            className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-indigo-500/10 text-indigo-300 border border-indigo-500/20 text-sm font-medium mb-4"
          >
            <Zap className="h-4 w-4" />
            <span>4PM CHAI LOVERS - Hackathon Project</span>
          </motion.div>

          <motion.h1 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.1 }}
            className="text-5xl md:text-7xl font-bold tracking-tight text-white leading-tight"
          >
            Run the <span className="text-transparent bg-clip-text bg-gradient-to-r from-indigo-400 to-cyan-400">right tests.</span><br/>
            Skip the rest.
          </motion.h1>

          <motion.p 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.2 }}
            className="text-lg md:text-xl text-slate-400 max-w-2xl mx-auto leading-relaxed"
          >
            Smart Test Impact Analysis (TIA) Engine. We analyze your Git commits and map dependencies to execute only the tests your changes actually break.
          </motion.p>

          <motion.div 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.3 }}
            className="flex flex-col sm:flex-row items-center justify-center gap-4 pt-4"
          >
            <button className="flex items-center gap-2 bg-white text-slate-950 px-8 py-3 rounded-full font-semibold hover:bg-slate-200 transition-colors w-full sm:w-auto">
              <PlayCircle className="h-5 w-5" />
              Simulate Pipeline
            </button>
            <button className="flex items-center gap-2 bg-slate-800 text-white border border-slate-700 px-8 py-3 rounded-full font-semibold hover:bg-slate-700 transition-colors w-full sm:w-auto">
              <GitBranch className="h-5 w-5" />
              View Repo
            </button>
          </motion.div>
        </div>
      </section>

      {/* Stats Section */}
      <section className="py-12 border-y border-white/5 bg-white/[0.02]">
        <div className="max-w-7xl mx-auto px-6 grid grid-cols-2 md:grid-cols-4 gap-8 divide-x divide-white/5 text-center">
          <div>
            <div className="text-4xl font-bold text-white mb-2">85%</div>
            <div className="text-sm font-medium text-slate-400">Avg. Time Saved</div>
          </div>
          <div>
            <div className="text-4xl font-bold text-white mb-2">10x</div>
            <div className="text-sm font-medium text-slate-400">Faster CI Builds</div>
          </div>
          <div>
            <div className="text-4xl font-bold text-white mb-2">AST</div>
            <div className="text-sm font-medium text-slate-400">Precision Mapping</div>
          </div>
          <div>
            <div className="text-4xl font-bold text-white mb-2">100%</div>
            <div className="text-sm font-medium text-slate-400">Coverage Retained</div>
          </div>
        </div>
      </section>

      {/* How it works */}
      <section id="how-it-works" className="py-24 max-w-7xl mx-auto px-6">
        <div className="text-center mb-16">
          <h2 className="text-3xl font-bold text-white mb-4">How it works</h2>
          <p className="text-slate-400 max-w-2xl mx-auto">From code commit to test execution, everything is optimized for speed without sacrificing confidence.</p>
        </div>

        <div className="grid md:grid-cols-3 gap-8">
          {[
            {
              icon: <GitCommit className="h-8 w-8 text-indigo-400" />,
              title: "1. Ingestion & Diff Extraction",
              desc: "We parse the Git commit history using GitPython to extract strictly modified files, functions, and lines."
            },
            {
              icon: <Code2 className="h-8 w-8 text-cyan-400" />,
              title: "2. AST Dependency Mapping",
              desc: "Using Python's ast module, we generate a comprehensive dependency graph linking source code changes to relevant test files."
            },
            {
              icon: <CheckCircle2 className="h-8 w-8 text-emerald-400" />,
              title: "3. Selective Execution",
              desc: "We dynamically construct the Pytest execution command to trigger only the targeted, impacted tests."
            }
          ].map((step, i) => (
            <div key={i} className="bg-slate-900/50 border border-white/5 rounded-2xl p-8 hover:bg-slate-900 transition-colors">
              <div className="bg-white/5 w-16 h-16 rounded-xl flex items-center justify-center mb-6">
                {step.icon}
              </div>
              <h3 className="text-xl font-semibold text-white mb-3">{step.title}</h3>
              <p className="text-slate-400 leading-relaxed">{step.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Dashboard Visualization Preview */}
      <section id="comparison" className="py-24 bg-slate-900/30 border-t border-white/5">
        <div className="max-w-7xl mx-auto px-6">
          <div className="flex flex-col md:flex-row items-center justify-between mb-12 gap-6">
            <div>
              <h2 className="text-3xl font-bold text-white mb-4">Execution Time Analysis</h2>
              <p className="text-slate-400 max-w-md">Compare standard full-suite pipeline executions vs. our Smart TIA pipeline runs across recent commits.</p>
            </div>
            <div className="flex gap-4">
              <div className="flex items-center gap-2 text-sm text-slate-400">
                <div className="w-3 h-3 rounded-full bg-slate-600"></div> Full Run
              </div>
              <div className="flex items-center gap-2 text-sm text-indigo-300">
                <div className="w-3 h-3 rounded-full bg-indigo-500"></div> Smart Run
              </div>
            </div>
          </div>

          <div className="bg-slate-950 border border-white/5 rounded-2xl p-6 h-[400px]">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={mockData} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
                <defs>
                  <linearGradient id="colorTime" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#475569" stopOpacity={0.8}/>
                    <stop offset="95%" stopColor="#475569" stopOpacity={0}/>
                  </linearGradient>
                  <linearGradient id="colorSmartTime" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#6366f1" stopOpacity={0.8}/>
                    <stop offset="95%" stopColor="#6366f1" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <XAxis dataKey="commit" stroke="#475569" fontSize={12} tickLine={false} axisLine={false} />
                <YAxis stroke="#475569" fontSize={12} tickLine={false} axisLine={false} unit="s" />
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
                <Tooltip 
                  contentStyle={{ backgroundColor: '#0f172a', borderColor: '#1e293b', borderRadius: '8px' }}
                  itemStyle={{ color: '#f8fafc' }}
                />
                <Area type="monotone" dataKey="time" name="Full Run Time" stroke="#475569" fillOpacity={1} fill="url(#colorTime)" />
                <Area type="monotone" dataKey="smartTime" name="Smart Run Time" stroke="#6366f1" fillOpacity={1} fill="url(#colorSmartTime)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-12 border-t border-white/5 text-center px-6">
        <div className="flex items-center justify-center gap-2 text-slate-500 mb-4">
          <Activity className="h-5 w-5" />
          <span className="font-semibold text-slate-400">SmartTIA</span>
        </div>
        <p className="text-sm text-slate-500">Built for the 4PM CHAI LOVERS Hackathon.</p>
      </footer>
    </div>
  );
}

export default App;
