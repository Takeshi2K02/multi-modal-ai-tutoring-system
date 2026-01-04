import React, { useState } from 'react';
import ScenarioControls from './components/Sidebar/ScenarioControls';
import TreeVisualizer from './components/Graph/TreeVisualizer';
import SignalsPanel from './components/Graph/SignalsPanel';
import StudentProfilePanel from './components/StudentProfilePanel';
import GoalDecomposition from './pages/GoalDecomposition';
import TOC from './pages/TableOfContents';
import { runSimulation } from './services/api';

function App() {
  const [view, setView] = useState('visualizer'); // 'visualizer' | 'decomposition' | 'toc'
  const [decompositionResult, setDecompositionResult] = useState(null); // Store data for TOC

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
      // Small artificial delay for visual smooth transitions if API is too fast
      // await new Promise(r => setTimeout(r, 600)); 

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

  // Route: Table of Contents (TOC)
  if (view === 'toc' && decompositionResult) {
    return <TOC data={decompositionResult} onBack={() => setView('decomposition')} />;
  }

  // Route: Goal Decomposition
  if (view === 'decomposition') {
    return (
      <GoalDecomposition
        onBack={() => setView('visualizer')}
        onStart={(data) => {
          setDecompositionResult(data);
          setView('toc');
        }}
      />
    );
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
      <button
        onClick={() => setView('decomposition')}
        className="absolute top-6 left-[380px] z-50 px-4 py-2 bg-white border border-slate-300 shadow-sm rounded-lg text-xs font-bold uppercase tracking-wider text-slate-600 hover:bg-slate-50 hover:text-indigo-600 transition-colors"
      >
        To Goal Decomposition →
      </button>

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
