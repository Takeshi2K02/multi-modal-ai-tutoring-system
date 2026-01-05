import React, { useState, useEffect } from 'react';
import { clsx } from 'clsx';
import { LayoutDashboard, BookOpen, BrainCircuit, Upload, Layers, ChevronRight, User } from 'lucide-react';
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

  // UI Toggle State
  const [showProfile, setShowProfile] = useState(true); // Requirement: Profile visible on start
  const [showCV, setShowCV] = useState(false);
  const [showRL, setShowRL] = useState(false);

  // Demo Mode State
  const [demoPersona, setDemoPersona] = useState(null);
  const [isDemoMode, setIsDemoMode] = useState(false);

  // MOCK PERSONAS for Demo with extended data
  const MOCK_PERSONAS = [
    {
      id: 'visual_confused',
      name: 'Alex (Visual Learner)',
      type: 'Visual',
      state: 'confused',
      traits: ['Needs Diagrams', 'Low Prior Knowledge'],
      cv_data: { emotion: 'Confused', engagement: 'Low', gaze: 'Scattered', posture: 'Slouched' },
      rl_data: { policy: 'Scaffolding', action: 'Breakdown Topic', confidence: 0.85 }
    },
    {
      id: 'textual_bored',
      name: 'Sam (Textual Learner)',
      type: 'Reading/Writing',
      state: 'bored',
      traits: ['Prefer Text', 'High Proficiency', 'Needs Challenge'],
      cv_data: { emotion: 'Bored', engagement: 'Medium', gaze: 'Away', posture: 'Relaxed' },
      rl_data: { policy: 'Gamification', action: 'Challenge Question', confidence: 0.92 }
    },
    {
      id: 'handson_curious',
      name: 'Jordan (Kinesthetic)',
      type: 'Kinesthetic',
      state: 'neutral',
      traits: ['Learn by Doing', 'Active Experimentation'],
      cv_data: { emotion: 'Curious', engagement: 'High', gaze: 'Focused', posture: 'Leaning In' },
      rl_data: { policy: 'Interactive', action: 'Simulation', confidence: 0.78 }
    }
  ];

  // Auto-Run Simulation on Agent View Entry
  useEffect(() => {
    if (view === 'agent' && currentTopicContext) {
      setIsDemoMode(true);
      setShowProfile(true);
      setShowCV(false);
      setShowRL(false);

      // 1. Select Random Persona (Single Source of Truth)
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
          <div className="flex h-full w-full relative overflow-hidden bg-slate-950">

            {/* LEFT EDGE BUTTON (Profile) */}
            <button
              onClick={() => setShowProfile(!showProfile)}
              className={`absolute left-0 top-1/2 -translate-y-1/2 z-50 py-8 px-1.5 rounded-r-xl border-y border-r border-slate-700/50 shadow-xl transition-all duration-300 flex flex-col items-center gap-2 ${showProfile ? 'bg-slate-800 text-white left-80 translate-x-[-1px]' : 'bg-slate-900/80 text-slate-500 hover:text-white hover:bg-slate-800 backdrop-blur'
                }`}
              style={{ writingMode: 'vertical-rl', textOrientation: 'mixed' }}
            >
              <div className="rotate-180 transform">{showProfile ? <ChevronRight size={14} /> : <User size={14} />}</div>
              <span className="text-[10px] font-bold uppercase tracking-widest mt-2">{showProfile ? 'Close' : 'Student'}</span>
            </button>


            {/* LEFT PANEL (Push) */}
            <div className={`h-full transition-all duration-300 ease-[cubic-bezier(0.25,0.1,0.25,1)] ${showProfile ? 'w-80 border-r border-slate-800' : 'w-0 border-none'} overflow-hidden bg-slate-900 relative z-40 shrink-0`}>
              <div className="w-80 h-full p-0">
                <StudentProfilePanel
                  profile={outcome?.meta?.profile}
                  tieBreakTrace={outcome?.meta?.tie_break_trace}
                  isDemoMode={isDemoMode}
                  demoPersona={demoPersona}
                />
              </div>
            </div>

            {/* CENTER GRAPH (Flexible) */}
            <div className="flex-1 relative h-full dots-pattern bg-slate-950 z-10 transition-all duration-300">
              <TreeVisualizer data={graphData} />

              {!graphData && !loading && !error && (
                <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
                  <div className="text-center space-y-4 opacity-30">
                    <div className="text-6xl grayscale">🌲</div>
                    <div className="text-xl font-light text-slate-500">
                      Agent Visualizer
                      <br />
                      <span className="text-base">Waiting for simulation...</span>
                    </div>
                  </div>
                </div>
              )}
            </div>

            {/* RIGHT PANEL (Push) - Transparent Container with Vertical 50/50 Zones */}
            {/* The logic: If EITHER is open, the container provides 72w width. 
                Inside, we have two 50% height zones. 
                If a card is closed, it fades out/scales down but the zone remains reserved (or empties out).
                User requested "Stack vertically with gap" if both open. 
                This implementation uses fixed 50/50 zones to ensure perfect alignment with the 25%/75% buttons.
            */}
            <div className={`h-full transition-all duration-300 ease-[cubic-bezier(0.25,0.1,0.25,1)] ${showCV || showRL ? 'w-72 border-none' : 'w-0 border-none'} overflow-hidden relative z-40 shrink-0`}>
              <div className="w-72 h-full flex flex-col bg-slate-950/20 backdrop-blur-sm">

                {/* Top Zone (CV) - 50% Height to align with Toggle */}
                <div className="h-1/2 w-full p-4 flex items-center justify-center relative">
                  <div className={`w-full max-h-full flex flex-col rounded-2xl border bg-slate-900 shadow-2xl overflow-hidden transition-all duration-300 ${showCV ? 'opacity-100 scale-100 border-emerald-500/30' : 'opacity-0 scale-95 border-transparent pointer-events-none absolute'} relative z-50`}>
                    {/* Header */}
                    <div className="bg-slate-950/80 p-3 border-b border-emerald-500/20 flex items-center justify-between">
                      <h3 className="text-[10px] font-bold uppercase tracking-widest text-emerald-400 flex items-center gap-2">
                        <span>📷</span> CV Input
                      </h3>
                      <div className="flex items-center gap-2">
                        <div className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></div>
                        <button onClick={() => setShowCV(false)} className="text-slate-500 hover:text-white transition-colors">
                          <span className="sr-only">Close</span>
                          <ChevronRight size={14} className="rotate-0 hover:rotate-90 transition-transform" />
                        </button>
                      </div>
                    </div>
                    {/* Body */}
                    <div className="p-3 overflow-y-auto custom-scrollbar">
                      {demoPersona?.cv_data ? (
                        <div className="space-y-2">
                          {Object.entries(demoPersona.cv_data).map(([k, v]) => (
                            <div key={k} className="bg-slate-950/40 p-2 rounded-lg border border-slate-800/60 flex flex-col">
                              <span className="text-[9px] text-slate-500 uppercase font-bold tracking-wider">{k}</span>
                              <span className="text-xs font-mono text-emerald-100/90">{v}</span>
                            </div>
                          ))}
                        </div>
                      ) : <div className="text-xs text-slate-500 italic p-2">No active signal</div>}
                    </div>
                  </div>
                </div>

                {/* Bottom Zone (RL) - 50% Height to align with Toggle */}
                <div className="h-1/2 w-full p-4 flex items-center justify-center relative border-t border-slate-800/0">
                  <div className={`w-full max-h-full flex flex-col rounded-2xl border bg-slate-900 shadow-2xl overflow-hidden transition-all duration-300 ${showRL ? 'opacity-100 scale-100 border-indigo-500/30' : 'opacity-0 scale-95 border-transparent pointer-events-none absolute'} relative z-50`}>
                    {/* Header */}
                    <div className="bg-slate-950/80 p-3 border-b border-indigo-500/20 flex items-center justify-between">
                      <h3 className="text-[10px] font-bold uppercase tracking-widest text-indigo-400 flex items-center gap-2">
                        <span>🤖</span> RL Policy
                      </h3>
                      <div className="flex items-center gap-2">
                        <div className="w-1.5 h-1.5 rounded-full bg-indigo-500 animate-pulse"></div>
                        <button onClick={() => setShowRL(false)} className="text-slate-500 hover:text-white transition-colors">
                          <span className="sr-only">Close</span>
                          <ChevronRight size={14} className="rotate-0 hover:rotate-90 transition-transform" />
                        </button>
                      </div>
                    </div>
                    {/* Body */}
                    <div className="p-3 overflow-y-auto custom-scrollbar">
                      {demoPersona?.rl_data ? (
                        <div className="space-y-2">
                          {Object.entries(demoPersona.rl_data).map(([k, v]) => (
                            <div key={k} className="bg-slate-950/40 p-2 rounded-lg border border-slate-800/60 flex flex-col">
                              <span className="text-[9px] text-slate-500 uppercase font-bold tracking-wider">{k}</span>
                              <span className="text-xs font-mono text-indigo-100/90">{v}</span>
                            </div>
                          ))}
                        </div>
                      ) : <div className="text-xs text-slate-500 italic p-2">No active signal</div>}
                    </div>
                  </div>
                </div>

              </div>
            </div>

            {/* RIGHT EDGE BUTTONS */}

            {/* CV Toggle (Top Quarter) */}
            <button
              onClick={() => setShowCV(!showCV)}
              className={`absolute top-[25%] -translate-y-1/2 z-50 py-6 px-1.5 rounded-l-xl border-y border-l border-slate-700/50 shadow-xl transition-all duration-300 flex flex-col items-center gap-2 ${showCV || showRL ? 'right-72 translate-x-[1px]' : 'right-0'
                } ${showCV ? 'bg-slate-800 text-white' : 'bg-slate-900/80 text-emerald-500/70 hover:text-emerald-400 hover:bg-slate-800 backdrop-blur'
                }`}
              style={{ writingMode: 'vertical-rl', textOrientation: 'mixed' }}
            >
              <div className="rotate-180 transform">{showCV ? <ChevronRight size={14} /> : <span className="text-lg">📷</span>}</div>
              <span className="text-[10px] font-bold uppercase tracking-widest mt-2">{showCV ? 'Close' : 'CV Input'}</span>
            </button>

            {/* RL Toggle (Bottom Quarter) */}
            <button
              onClick={() => setShowRL(!showRL)}
              className={`absolute top-[75%] -translate-y-1/2 z-50 py-6 px-1.5 rounded-l-xl border-y border-l border-slate-700/50 shadow-xl transition-all duration-300 flex flex-col items-center gap-2 ${showCV || showRL ? 'right-72 translate-x-[1px]' : 'right-0'
                } ${showRL ? 'bg-slate-800 text-white' : 'bg-slate-900/80 text-indigo-500/70 hover:text-indigo-400 hover:bg-slate-800 backdrop-blur'
                }`}
              style={{ writingMode: 'vertical-rl', textOrientation: 'mixed' }}
            >
              <div className="rotate-180 transform">{showRL ? <ChevronRight size={14} /> : <span className="text-lg">🤖</span>}</div>
              <span className="text-[10px] font-bold uppercase tracking-widest mt-2">{showRL ? 'Close' : 'RL Input'}</span>
            </button>

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
