import React, { useState } from 'react';
import { clsx } from 'clsx';
import { LayoutDashboard, BookOpen, BrainCircuit, Upload, Layers } from 'lucide-react';
import TreeVisualizer from './components/Graph/TreeVisualizer';
import ScenarioControls from './components/Sidebar/ScenarioControls';
import StudentProfilePanel from './components/StudentProfilePanel';
import SignalsPanel from './components/Graph/SignalsPanel';
import LectureUpload from './pages/LectureUpload';
import GoalDecomposition from './pages/GoalDecomposition';
import LearningSession from './pages/LearningSession';
import SessionDashboard from './pages/SessionDashboard';

function App() {
  const [view, setView] = useState('decomposition'); // Default: 'decomposition'
  const [activeSessionId, setActiveSessionId] = useState(null);

  // Agent State
  const [graphData, setGraphData] = useState(null);
  const [outcome, setOutcome] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleRun = async (scenario) => {
    setLoading(true);
    setError(null);
    setGraphData(null);
    setOutcome(null);

    try {
      const { runSimulation } = await import('./services/api');
      const result = await runSimulation(scenario);
      setGraphData(result);
      setOutcome(result);
    } catch (err) {
      console.error(err);
      const msg = err.response?.data?.detail || err.message || "Failed to connect to Agent backend.";
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  // --- Views ---

  const renderContent = () => {
    switch (view) {
      case 'decomposition':
        return (
          <GoalDecomposition
            onBack={() => setView('agent')} // Optional Link
            onStart={(sessionId) => {
              setActiveSessionId(sessionId);
              setView('session');
            }}
          />
        );

      case 'session':
        if (!activeSessionId) return <div className='p-10 text-slate-500'>No active session selected.</div>;
        return (
          <LearningSession
            sessionId={activeSessionId}
            onBack={() => setView('dashboard')}
          />
        );

      case 'dashboard':
        return (
          <SessionDashboard
            onBack={() => setView('decomposition')}
            onResume={(sessId) => {
              setActiveSessionId(sessId);
              setView('session');
            }}
          />
        );

      case 'upload':
        return <LectureUpload onBack={() => setView('decomposition')} />;

      case 'agent':
        return (
          <div className="flex h-full w-full relative">
            <ScenarioControls onRun={handleRun} isRunning={loading} outcome={outcome} />

            <div className="flex-1 relative h-full dots-pattern bg-slate-950">
              <TreeVisualizer data={graphData} />
              <SignalsPanel data={graphData?.meta?.context_data} />

              <div className="absolute bottom-6 right-6 w-80 z-40 max-h-[400px] flex flex-col pointer-events-none">
                <div className="pointer-events-auto shadow-xl h-full flex flex-col glass-panel rounded-xl overflow-hidden">
                  <StudentProfilePanel profile={graphData?.meta?.profile} tieTrace={graphData?.meta?.tie_break_trace} />
                </div>
              </div>

              {error && (
                <div className="absolute top-6 left-1/2 -translate-x-1/2 z-50 bg-red-900/90 backdrop-blur border-l-4 border-red-500 shadow-xl px-6 py-4 rounded-r-lg flex items-center gap-3 animate-bounce">
                  <span className="text-red-500 text-xl">⚠️</span>
                  <div>
                    <h4 className="font-bold text-red-100 text-sm">Connection Error</h4>
                    <p className="text-xs text-red-200">{error}</p>
                  </div>
                  <button onClick={() => setError(null)} className="ml-4 text-slate-400 hover:text-slate-200">×</button>
                </div>
              )}

              {!graphData && !loading && !error && (
                <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
                  <div className="text-center space-y-4 opacity-30">
                    <div className="text-6xl grayscale">🌲</div>
                    <div className="text-xl font-light text-slate-500">
                      Agent Visualizer
                      <br />
                      <span className="text-base">Select a scenario to inspect reasoning.</span>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        );

      default:
        return <div>Unknown View</div>;
    }
  };

  return (
    <div className="flex flex-col h-screen w-screen bg-slate-950 text-slate-50 overflow-hidden font-sans">
      {/* Top Global Nav */}
      <nav className="h-16 border-b border-slate-800 bg-slate-900/80 backdrop-blur-md flex items-center justify-between px-6 shrink-0 z-50">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center shadow-lg shadow-indigo-500/20">
            <BrainCircuit className="text-white w-5 h-5" />
          </div>
          <h1 className="font-bold text-lg tracking-tight text-slate-100">Antigravity<span className="text-indigo-400">Tutor</span></h1>
        </div>

        <div className="flex items-center gap-1 bg-slate-800/50 p-1 rounded-lg border border-slate-700/50">
          <NavButton
            active={view === 'decomposition' || view === 'upload'}
            onClick={() => setView('decomposition')}
            icon={<BookOpen size={18} />}
            label="Plan & Decompose"
          />
          <NavButton
            active={view === 'dashboard' || view === 'session'}
            onClick={() => setView('dashboard')}
            icon={<Layers size={18} />}
            label="My Learning"
          />
          <NavButton
            active={view === 'agent'}
            onClick={() => setView('agent')}
            icon={<BrainCircuit size={18} />}
            label="Agent Internals"
          />
        </div>

        <div className="flex items-center gap-4">
          <button
            onClick={() => setView('upload')}
            className="flex items-center gap-2 text-xs font-bold text-slate-400 hover:text-indigo-400 transition-colors"
          >
            <Upload size={14} />
            <span>Upload Context</span>
          </button>
        </div>
      </nav>

      {/* Main Content Area */}
      <main className="flex-1 overflow-hidden relative">
        {renderContent()}
      </main>
    </div>
  );
}

const NavButton = ({ active, onClick, icon, label }) => (
  <button
    onClick={onClick}
    className={clsx(
      "flex items-center gap-2 px-4 py-2 rounded-md text-sm font-medium transition-all",
      active
        ? "bg-slate-700 text-white shadow-sm"
        : "text-slate-400 hover:text-slate-200 hover:bg-slate-800"
    )}
  >
    {icon}
    <span>{label}</span>
  </button>
);

export default App;
