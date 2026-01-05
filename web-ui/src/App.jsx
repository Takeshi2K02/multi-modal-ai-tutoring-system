import React, { useState } from 'react';
import TreeVisualizer from './components/Graph/TreeVisualizer';
import ScenarioControls from './components/Sidebar/ScenarioControls';
import NodeDetail from './components/Panel/NodeDetail';
import StudentProfilePanel from './components/StudentProfilePanel';
import SignalsPanel from './components/Graph/SignalsPanel';
import LectureUpload from './pages/LectureUpload';
import GoalDecomposition from './pages/GoalDecomposition';
import LearningSession from './pages/LearningSession';
import SessionDashboard from './pages/SessionDashboard';

function App() {
  const [activeNode, setActiveNode] = useState(null);
  const [view, setView] = useState('agent'); // 'agent', 'goal', 'session', 'dashboard'
  const [activeSessionId, setActiveSessionId] = useState(null);

  const [graphData, setGraphData] = useState(null);
  const [outcome, setOutcome] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Re-import runSimulation if needed? No, need to import it at top.
  // Wait, I need to check imports. `import { runSimulation } from './services/api';` is NOT in the file currently (lines 1-13)

  const handleRun = async (scenario) => {
    setLoading(true);
    setError(null);
    setGraphData(null);
    setOutcome(null);

    try {
      // Import this dynamically or assume it's imported? 
      // I need to add the import statement too.
      // But replace_file_content is for contiguous block.
      // I will do two edits or one large one.
      // Let's assume import is missing too.
      // I will handle imports in a separate call or check if I can just add it here?
      // No, imports are at top.
      const { runSimulation } = await import('./services/api'); // Dynamic import to avoid messing up top-level replacer?
      // Or I can just trust that I will add it.

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

  // Route: Active Learning Session
  if (view === 'session' && activeSessionId) {
    return (
      <LearningSession
        sessionId={activeSessionId}
        onBack={() => setView('dashboard')}
      />
    );
  }

  // Route: Goal Decomposition
  if (view === 'decomposition') {
    return (
      <GoalDecomposition
        onBack={() => setView('visualizer')}
        onStart={(sessionId) => {
          setActiveSessionId(sessionId);
          setView('session');
        }}
      />
    );
  }

  if (view === 'dashboard') {
    return (
      <SessionDashboard
        onBack={() => setView('agent')}
        onResume={(sessId) => {
          setActiveSessionId(sessId);
          setView('session');
        }}
      />
    );
  }

  // Route: Lecture Upload
  if (view === 'upload') {
    return <LectureUpload onBack={() => setView('visualizer')} />;
  }

  // Route: Main Visualizer
  return (
    <div className="flex h-screen w-screen bg-slate-50 overflow-hidden font-sans text-slate-900">

      {/* Left Sidebar */}
      <ScenarioControls
        onRun={handleRun}
        isRunning={loading}
        outcome={outcome}
      />

      {/* Absolute Nav Button for Decomposition Demo */}
      <div className="absolute top-6 left-[380px] z-50 flex gap-2">
        <button
          onClick={() => setView('dashboard')}
          className="px-4 py-2 bg-indigo-50 border border-indigo-200 shadow-sm rounded-lg text-xs font-bold uppercase tracking-wider text-indigo-700 hover:bg-indigo-100 transition-colors flex items-center gap-2"
        >
          <span>📚</span> My Learning
        </button>

        <button
          onClick={() => setView('decomposition')}
          className="px-4 py-2 bg-white border border-slate-300 shadow-sm rounded-lg text-xs font-bold uppercase tracking-wider text-slate-600 hover:bg-slate-50 hover:text-indigo-600 transition-colors"
        >
          To Goal Decomposition →
        </button>

        <button
          onClick={() => setView('upload')}
          className="px-4 py-2 bg-white border border-slate-300 shadow-sm rounded-lg text-xs font-bold uppercase tracking-wider text-slate-600 hover:bg-slate-50 hover:text-emerald-600 transition-colors"
        >
          📂 Upload Lectures
        </button>
      </div>

      {/* Main Graph Area */}
      <div className="flex-1 relative h-full dots-pattern">

        {/* Graph Canvas */}
        <TreeVisualizer data={graphData} />

        {/* Context / Signals Panel (Top Right) */}
        <SignalsPanel data={graphData?.meta?.context_data} />

        {/* Student Profile Panel (Bottom Right) */}
        <div className="absolute bottom-6 right-6 w-80 z-40 max-h-[400px] flex flex-col pointer-events-none">
          <div className="pointer-events-auto shadow-xl h-full flex flex-col">
            <StudentProfilePanel
              profile={graphData?.meta?.profile}
              tieTrace={graphData?.meta?.tie_break_trace}
            />
          </div>
        </div>

        {/* Error Toast */}
        {error && (
          <div className="absolute top-6 left-1/2 -translate-x-1/2 z-50 bg-white/90 backdrop-blur border-l-4 border-red-500 shadow-xl px-6 py-4 rounded-r-lg flex items-center gap-3 animate-bounce">
            <span className="text-red-500 text-xl">⚠️</span>
            <div>
              <h4 className="font-bold text-red-700 text-sm">Connection Error</h4>
              <p className="text-xs text-red-600">{error}</p>
            </div>
            <button onClick={() => setError(null)} className="ml-4 text-slate-400 hover:text-slate-600">×</button>
          </div>
        )}

        {/* Empty State Call to Action */}
        {!graphData && !loading && !error && (
          <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
            <div className="text-center space-y-4 opacity-40">
              <div className="text-6xl">🌲</div>
              <div className="text-xl font-light text-slate-500">
                Ready to visualize thought process.
                <br />
                <span className="text-base">Select a scenario on the left to begin.</span>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default App;
