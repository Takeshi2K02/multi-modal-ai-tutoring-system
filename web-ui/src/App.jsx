import React, { useState } from 'react';
import ScenarioControls from './components/Sidebar/ScenarioControls';
import TreeVisualizer from './components/Graph/TreeVisualizer';
import { runSimulation } from './services/api';

function App() {
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

  return (
    <div className="flex h-screen w-screen bg-slate-50 overflow-hidden font-sans text-slate-900">

      {/* Left Sidebar */}
      <ScenarioControls
        onRun={handleRun}
        isRunning={loading}
        outcome={outcome}
      />

      {/* Main Graph Area */}
      <div className="flex-1 relative h-full dots-pattern">

        {/* Graph Canvas */}
        <TreeVisualizer data={graphData} />

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
