import React, { useState, useEffect } from 'react';
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
import Navbar from './components/Navbar';

function App() {
  const [view, setView] = useState('decomposition'); // Default: 'decomposition'
  const [activeSessionId, setActiveSessionId] = useState(null);
  const [currentTopicContext, setCurrentTopicContext] = useState(null);

  // Dynamic Title
  useEffect(() => {
    const titles = {
      decomposition: 'EduSynth - Plan',
      session: 'EduSynth - Learning',
      dashboard: 'EduSynth - My Learning',
      agent: 'EduSynth - Agent View',
      upload: 'EduSynth - Upload'
    };
    document.title = titles[view] || 'EduSynth AI Tutor';
  }, [view]);

  // Agent State
  const [graphData, setGraphData] = useState(null);
  const [outcome, setOutcome] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Demo Mode State
  const [demoPersona, setDemoPersona] = useState(null);
  const [isDemoMode, setIsDemoMode] = useState(false);

  // MOCK PERSONAS for Demo
  const MOCK_PERSONAS = [
    { id: 'visual_confused', name: 'Alex (Visual Learner)', type: 'Visual', state: 'confused', traits: ['Needs Diagrams', 'Low Prior Knowledge'] },
    { id: 'textual_bored', name: 'Sam (Textual Learner)', type: 'Reading/Writing', state: 'bored', traits: ['Prefer Text', 'High Proficiency', 'Needs Challenge'] },
    { id: 'handson_curious', name: 'Jordan (Kinesthetic)', type: 'Kinesthetic', state: 'neutral', traits: ['Learn by Doing', 'Active Experimentation'] }
  ];

  // Auto-Run Simulation on Agent View Entry
  useEffect(() => {
    if (view === 'agent' && currentTopicContext) {
      setIsDemoMode(true);

      // 1. Select Random Persona
      const randomPersona = MOCK_PERSONAS[Math.floor(Math.random() * MOCK_PERSONAS.length)];
      setDemoPersona(randomPersona);
      console.log("Demo Mode: Persona Selected", randomPersona);

      // 2. Auto-Run Simulation
      // We add a small delay for visual effect so the user sees the transition
      const timer = setTimeout(() => {
        handleRun(randomPersona.state); // Use the persona's state to drive the sim logic
      }, 1000);

      return () => clearTimeout(timer);
    } else {
      setIsDemoMode(false);
    }
  }, [view, currentTopicContext]);

  const handleRun = async (scenario) => {
    setLoading(true);
    setError(null);
    setGraphData(null);
    setOutcome(null);

    try {
      const { runSimulation } = await import('./services/api');
      // Pass the current topic context if available
      const result = await runSimulation(scenario, currentTopicContext);
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
            onStartLearning={(topic) => {
              setCurrentTopicContext(topic);
              setView('agent');
            }}
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
            <ScenarioControls
              onRun={handleRun}
              isRunning={loading}
              outcome={outcome}
              topicContext={currentTopicContext}
              isDemoMode={isDemoMode}
              demoPersona={demoPersona}
            />

            <div className="flex-1 relative h-full dots-pattern bg-slate-950">
              <TreeVisualizer data={graphData} />

              {/* Floating Signals Panel */}
              <div className="absolute top-5 right-5 z-10 w-80 pointer-events-none">
                <div className="pointer-events-auto transition-transform hover:scale-105">
                  <SignalsPanel outcomeStatus={outcome?.meta?.context_data} />
                </div>
              </div>
              {/* Student Profile Panel (Floating Demo Card) */}
              <div className="absolute bottom-5 right-5 z-10 w-96 pointer-events-none flex flex-col gap-4">
                <div className="pointer-events-auto transition-transform hover:scale-105">
                  <StudentProfilePanel
                    profile={outcome?.meta?.profile}
                    tieBreakTrace={outcome?.meta?.tie_break_trace}
                    isDemoMode={isDemoMode}
                    demoPersona={demoPersona}
                  />
                </div>
              </div>

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
      {/* Global Navbar */}
      <Navbar currentView={view} onViewChange={setView} />

      {/* Main Content Area */}
      <div className="flex-1 overflow-hidden relative">
        {renderContent()}
      </div>
    </div>
  );
}

export default App;
