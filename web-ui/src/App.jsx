import React, { useState, useEffect } from 'react';
import { clsx } from 'clsx';
import { io } from 'socket.io-client';
import { motion, AnimatePresence } from 'framer-motion';
import { LayoutDashboard, BookOpen, BrainCircuit, Upload, Layers, ChevronRight, ChevronLeft, User, Database, Camera, Bot } from 'lucide-react';
import useSWR from 'swr';
import { fetcher, API_BASE_URL } from './services/api';
import TreeVisualizer from './components/Graph/TreeVisualizer';
import ScenarioControls from './components/Sidebar/ScenarioControls';
import StudentProfilePanel from './components/StudentProfilePanel';
import SignalsPanel from './components/Graph/SignalsPanel';
import LectureUpload from './pages/LectureUpload';
import GoalDecomposition from './pages/GoalDecomposition';
import CurriculumBrowser from './pages/CurriculumBrowser';
import LessonView from './pages/LessonView';
import SessionDashboard from './pages/SessionDashboard';
import Navbar from './components/Navbar';

// import ContentGeneration from './pages/ContentGeneration'; // Replaced by LessonView
import AdminMonitor from './components/AdminMonitor';
import DataDashboard from './pages/DataDashboard';
import LearningLayout from './components/LearningLayout';
import LiveAffectSensing from './components/LiveAffectSensing';
import { ThemeProvider } from './context/ThemeContext';

const socket = io('http://localhost:8000');

function App() {
  const [view, setView] = useState('decomposition'); // Default: 'decomposition'
  const [activeSessionId, setActiveSessionId] = useState(null);
  const [currentTopicContext, setCurrentTopicContext] = useState(null);
  const [isLessonReady, setIsLessonReady] = useState(false);
  const [contentGenRequest, setContentGenRequest] = useState(null); // New State
  const [countdown, setCountdown] = useState(0); // New State

  // Dynamic Title
  useEffect(() => {
    const titles = {
      decomposition: 'EduSynth - Plan',
      curriculum: 'EduSynth - Curriculum',
      lesson: 'EduSynth - Lesson',
      dashboard: 'EduSynth - My Learning',
      agent: 'EduSynth - Agent View',
      upload: 'EduSynth - Upload',
      monitor: 'EduSynth - Admin Monitor',
      data: 'EduSynth - Data Center'
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

  // 1. Analytics Data Hooks
  const { data: analytics } = useSWR(`${API_BASE_URL}/api/analytics/historical?user_id=alex_123`, fetcher);
  const { data: latest } = useSWR(`${API_BASE_URL}/api/analytics/latest?user_id=alex_123`, fetcher, { refreshInterval: 2000 });

  const cvStats = analytics?.cv_stats || {};
  const rlStats = analytics?.rl_stats || {};
  const latestCv = latest?.cv || {};
  const latestRl = latest?.rl || {};

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
      setCountdown(0);
      setContentGenRequest(null);

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
    setCountdown(0);

    try {
      const { runSimulation } = await import('./services/api');
      // Pass the current topic context if available
      const result = await runSimulation(scenario, currentTopicContext);
      setGraphData(result);
      setOutcome(result);
      // NOTE: Simulation complete, but we wait for VISUAL playback to finish before countdown.
    } catch (err) {
      console.error(err);
      const msg = err.response?.data?.detail || err.message || "Failed to connect to Agent backend.";
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  const handleSimulationComplete = () => {
    // Triggered by TreeVisualizer onAnimationComplete
    if (countdown > 0) return; // Already counting down

    // Construct Payload
    if (!outcome || !demoPersona) return;

    // Find the directive from the best node in the ToT graph
    const bestNodeId = outcome.meta?.best_path_ids?.[outcome.meta.best_path_ids.length - 1];
    const bestNode = outcome.nodes?.find(n => n.id === bestNodeId);
    const directive = bestNode?.data?.directive || {
      type: "explanation",
      content: outcome.meta?.final_response || "No structured content available."
    };

    const requestPayload = {
      topic: currentTopicContext || { title: "Introduction to Calculus", id: "calc_101" },
      studentPersona: {
        id: demoPersona.id,
        name: demoPersona.name,
        traits: demoPersona.traits
      },
      selectedStrategy: {
        pathId: outcome.meta?.best_path_id || "path_optimal",
        pathTitle: outcome.meta?.strategy_name || "Adaptive Scaffolding",
        techniques: outcome.meta?.techniques || ["Metaphor", "Step-by-Step"],
        tone: outcome.meta?.tone || "Encouraging",
        format: "Interactive Module",
        stepPlan: ["Intro", "Concept", "Practice"]
      },
      directive, // Pass the structured ToT output
      difficultySignal: {
        reason: demoPersona.state,
        evidence: {
          cvInput: demoPersona.cv_data,
          rlInput: demoPersona.rl_data
        }
      },
      outputSpec: {
        sections: ["Explanation", "Worked Example", "Quick Check", "Summary"],
        length: "medium",
        style: demoPersona.type === 'Visual' ? 'interactive' : 'direct'
      }
    };

    setContentGenRequest(requestPayload);
    setCountdown(10); // Start 10s countdown
  };

  // Countdown Effect
  useEffect(() => {
    if (countdown > 0) {
      const timer = setTimeout(() => setCountdown(c => c - 1), 1000);
      return () => clearTimeout(timer);
    } else if (countdown === 0 && contentGenRequest && view === 'agent') {
      // Countdown finished, navigate!
      setView('content-generation');
    }
  }, [countdown, contentGenRequest, view]);


  // --- Views ---

  const renderContent = () => {
    switch (view) {
      case 'decomposition':
        return (
          <GoalDecomposition
            onBack={() => setView('agent')} // Optional Link
            onStart={(sessionId) => {
              setActiveSessionId(sessionId);
              setView('dashboard'); // Navigate to "My Knowledge Paths" view
            }}
          />
        );

      case 'curriculum':
        if (!activeSessionId) return <div className='p-10 text-zinc-500'>No active session selected.</div>;
        return (
          <CurriculumBrowser
            sessionId={activeSessionId}
            onBack={() => setView('dashboard')}
            onContinue={(topic) => {
              setCurrentTopicContext(topic);
              setIsLessonReady(false); // Reset for next lesson
              setView('lesson');
            }}
          />
        );

      case 'lesson':
        if (!activeSessionId || !currentTopicContext) return <div className='p-10 text-zinc-500'>Module data missing.</div>;
        return (
          <LessonView
            key={currentTopicContext?.id || currentTopicContext?.title || 'active-module'}
            sessionId={activeSessionId}
            topic={currentTopicContext}
            onBack={() => {
              setIsLessonReady(false);
              setView('curriculum');
            }}
            onReady={() => setIsLessonReady(true)}
            sio={socket}
          />
        );

      case 'dashboard':
        return (
          <SessionDashboard
            onBack={() => setView('decomposition')}
            onResume={(sessId) => {
              setActiveSessionId(sessId);
              setView('curriculum');
            }}
          />
        );

      case 'upload':
        return (
          <LectureUpload
            onBack={() => setView('decomposition')}
            onSuccess={() => setView('decomposition')}
          />
        );

      case 'monitor':
        return <AdminMonitor />;

      case 'data':
        return <DataDashboard />;

      case 'agent':
        return (
          <div className="flex h-full w-full relative overflow-hidden bg-zinc-950 dark:bg-edu-bg-dark selection:bg-primary/30 transition-colors">

            {/* LEFT EDGE TOGGLE (Student Profile) */}
            <button
              onClick={() => setShowProfile(!showProfile)}
              className={`absolute top-1/2 -translate-y-1/2 z-50 py-10 px-2 rounded-r-2xl border-y border-r border-edu-border-light dark:border-[#90E0EF]/10 shadow-2xl transition-all duration-500 flex flex-col items-center gap-4 ${showProfile ? 'left-80' : 'left-0'
                } ${showProfile ? 'bg-white/60 dark:bg-[#1E293B]/20 text-edu-text-light dark:text-edu-text-dark backdrop-blur-3xl' : 'bg-edu-surface-light dark:bg-[#1E293B]/60 text-primary backdrop-blur hover:bg-edu-bg-light dark:hover:bg-[#1E293B]/80'
                }`}
            >
              <div className="flex flex-col items-center gap-4">
                {showProfile ? <ChevronLeft size={16} /> : <User size={18} />}
                <span className="text-[10px] font-black uppercase tracking-[0.3em] [writing-mode:vertical-lr] rotate-180">
                  {showProfile ? 'Close' : 'Student'}
                </span>
              </div>
            </button>


            {/* LEFT PANEL (Overlay) */}
            <div className={`absolute top-0 left-0 h-full transition-all duration-500 ease-[cubic-bezier(0.25,0.1,0.25,1)] ${showProfile ? 'w-80 translate-x-0' : 'w-80 -translate-x-full'} z-40 bg-white/95 dark:bg-[#1E293B]/15 backdrop-blur-3xl border-r border-edu-border-light dark:border-[#90E0EF]/10 shadow-2xl transition-colors`}>
              <StudentProfilePanel
                profile={outcome?.meta?.profile || {
                  name: "Alex (Real)",
                  mastery_level: "Sophomore",
                  learning_preferences: analytics?.preferences || {}
                }}
                tieTrace={outcome?.meta?.tie_break_trace}
                isDemoMode={isDemoMode}
                demoPersona={demoPersona}
              />
            </div>

            {/* CENTER GRAPH (Centered) */}
            <div className="flex-1 relative h-full dots-pattern bg-edu-bg-light dark:bg-edu-bg-dark z-10 transition-colors duration-300">
              <TreeVisualizer
                data={graphData}
                onAnimationComplete={() => {
                  if (graphData && !contentGenRequest) {
                    handleSimulationComplete();
                  }
                }}
              />
              {!graphData && !loading && !error && (
                <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
                  <div className="text-center space-y-4 opacity-30">
                    <div className="text-6xl grayscale filter contrast-125">🌲</div>
                    <div className="text-xl font-light text-zinc-500 dark:text-slate-500">
                      Agent Visualizer
                      <br />
                      <span className="text-base">Waiting for simulation...</span>
                    </div>
                  </div>
                </div>
              )}

              {/* Status Overlay & Countdown */}
              {countdown > 0 && (
                <div className="absolute top-8 left-1/2 -translate-x-1/2 bg-primary dark:bg-primary/90 text-white backdrop-blur-md px-6 py-3 rounded-full shadow-2xl border border-primary/20 dark:border-primary/50 flex items-center gap-4 z-50 animate-in fade-in slide-in-from-top-4 transition-all">
                  <div className="relative w-5 h-5">
                    <svg className="w-full h-full -rotate-90">
                      <circle cx="10" cy="10" r="8" fill="none" stroke="currentColor" strokeWidth="2" className="text-primary-dark opacity-30" />
                      <circle cx="10" cy="10" r="8" fill="none" stroke="currentColor" strokeWidth="2" strokeDasharray="50" strokeDashoffset={50 - (50 * countdown) / 10} className="text-secondary transition-all duration-1000 ease-linear" />
                    </svg>
                  </div>
                  <div className="flex flex-col">
                    <span className="text-xs font-bold uppercase tracking-wider text-white/70">Simulation Complete</span>
                    <span className="text-sm font-medium">Preparing learning content... {countdown}s</span>
                  </div>
                </div>
              )}
            </div>

            {/* RIGHT PANEL (Overlay) */}
            <div className={`absolute top-0 right-0 h-full transition-all duration-500 ease-[cubic-bezier(0.25,0.1,0.25,1)] ${showCV || showRL ? 'w-80 translate-x-0' : 'w-80 translate-x-full'} z-40 bg-white/95 dark:bg-[#1E293B]/15 backdrop-blur-3xl border-l border-edu-border-light dark:border-[#90E0EF]/10 shadow-2xl transition-colors`}>
              <div className="h-full flex flex-col p-4 gap-4">
                {/* CV Panel Fragment */}
                <div className={`flex-1 transition-all duration-500 ${showCV ? 'opacity-100 scale-100' : 'opacity-0 scale-95 pointer-events-none'}`}>
                  <div className="h-full flex flex-col rounded-[32px] border border-secondary/20 bg-zinc-50 dark:bg-white/[0.02] overflow-hidden shadow-sm dark:shadow-none transition-colors">
                    <div className="p-4 border-b border-edu-border-light dark:border-white/5 flex justify-between items-center bg-secondary/5 transition-colors">
                      <span className="text-[10px] font-black tracking-widest text-secondary uppercase transition-colors">CV ANALYTICS</span>
                      <button onClick={() => setShowCV(false)}><ChevronRight size={14} className="text-zinc-400 dark:text-slate-500 transition-colors" /></button>
                    </div>
                    <div className="p-4 overflow-y-auto custom-scrollbar">
                      <div className="space-y-6">
                        <div className="p-4 bg-white dark:bg-white/[0.01] rounded-2xl border border-edu-border-light dark:border-white/5 group hover:border-secondary/30 transition-all duration-300">
                          <span className="text-[9px] text-zinc-400 dark:text-slate-500 block mb-1 font-black tracking-widest uppercase transition-colors">Latest Engagement</span>
                          <span className="text-3xl font-mono text-secondary transition-colors">{latestCv.engagement_score || '0.00'}</span>
                        </div>
                        <div className="space-y-3">
                          <span className="text-[9px] text-zinc-400 dark:text-slate-500 block font-black tracking-widest uppercase transition-colors">Current Affect</span>
                          <div className="p-4 bg-secondary/5 rounded-[24px] border border-secondary/20 flex justify-between items-center group transition-all duration-500">
                            <span className="text-lg font-light text-edu-text-light dark:text-secondary-100 capitalize tracking-tight transition-colors">{latestCv.emotion || 'Neutral'}</span>
                            <div className="w-2.5 h-2.5 rounded-full bg-secondary animate-pulse shadow-[0_0_12px_rgba(16,185,129,0.5)] transition-colors" />
                          </div>
                          <div className="text-[9px] font-mono text-zinc-400 dark:text-slate-600 text-right opacity-50 transition-colors">
                            SIGNAL SYNCED: {latestCv.timestamp ? new Date(latestCv.timestamp).toLocaleTimeString() : 'Awaiting...'}
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>

                {/* RL Panel Fragment */}
                <div className={`flex-1 transition-all duration-500 ${showRL ? 'opacity-100 scale-100' : 'opacity-0 scale-95 pointer-events-none'}`}>
                  <div className="h-full flex flex-col rounded-[32px] border border-primary/20 bg-zinc-50 dark:bg-white/[0.02] overflow-hidden shadow-sm dark:shadow-none transition-colors">
                    <div className="p-4 border-b border-edu-border-light dark:border-white/5 flex justify-between items-center bg-primary/5 transition-colors">
                      <span className="text-[10px] font-black tracking-widest text-primary uppercase transition-colors">RL STRATEGY</span>
                      <button onClick={() => setShowRL(false)}><ChevronRight size={14} className="text-zinc-400 dark:text-slate-500 transition-colors" /></button>
                    </div>
                    <div className="p-4 overflow-y-auto custom-scrollbar">
                      <div className="space-y-6">
                        <div className="p-4 bg-white dark:bg-white/[0.01] rounded-2xl border border-edu-border-light dark:border-white/5 group hover:border-primary/30 transition-all duration-300">
                          <span className="text-[9px] text-zinc-400 dark:text-slate-500 block mb-1 font-black tracking-widest uppercase transition-colors">Strategy Confidence</span>
                          <span className="text-3xl font-mono text-primary transition-colors">{latestRl.confidence ? (latestRl.confidence * 100).toFixed(0) + '%' : '0%'}</span>
                        </div>
                        <div className="space-y-3">
                          <span className="text-[9px] text-zinc-400 dark:text-slate-500 block font-black tracking-widest uppercase transition-colors">Deciding Policy</span>
                          <div className="p-4 bg-primary/5 rounded-[24px] border border-primary/20 group transition-all duration-500">
                            <span className="text-sm font-medium text-edu-text-light dark:text-primary-100 capitalize mb-1 block transition-colors">{latestRl.action || 'Idle'}</span>
                            <span className="text-[10px] text-zinc-500 dark:text-slate-500 line-clamp-2 italic font-light leading-relaxed transition-colors">
                              {latestRl.reasoning || "Observing student patterns for optimal intervention path."}
                            </span>
                          </div>
                          <div className="text-[9px] font-mono text-zinc-400 dark:text-slate-600 text-right opacity-50 transition-colors">
                            POLICY UPDATED: {latestRl.timestamp ? new Date(latestRl.timestamp).toLocaleTimeString() : 'Awaiting...'}
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* RIGHT EDGE BUTTONS */}

            {/* CV Toggle (Top Quarter) */}
            <button
              onClick={() => setShowCV(!showCV)}
              className={`absolute top-[30%] -translate-y-1/2 z-50 py-8 px-2 rounded-l-2xl border-y border-l border-edu-border-light dark:border-[#90E0EF]/10 shadow-2xl transition-all duration-300 flex flex-col items-center gap-4 ${showCV || showRL ? 'right-80' : 'right-0'
                } ${showCV ? 'bg-white/60 dark:bg-[#1E293B]/15 text-secondary backdrop-blur-3xl' : 'bg-edu-surface-light dark:bg-[#1E293B]/40 text-secondary/70 hover:text-secondary hover:bg-edu-bg-light dark:hover:bg-[#1E293B]/60 backdrop-blur'
                }`}
            >
              <div className="flex flex-col items-center gap-4">
                {showCV ? <ChevronRight size={16} /> : <Camera size={18} />}
                <span className="text-[10px] font-black uppercase tracking-[0.2em] [writing-mode:vertical-lr] rotate-180">
                  {showCV ? 'Close' : 'CV Input'}
                </span>
              </div>
            </button>

            {/* RL Toggle (Bottom Quarter) */}
            <button
              onClick={() => setShowRL(!showRL)}
              className={`absolute top-[70%] -translate-y-1/2 z-50 py-8 px-2 rounded-l-2xl border-y border-l border-edu-border-light dark:border-[#90E0EF]/10 shadow-2xl transition-all duration-300 flex flex-col items-center gap-4 ${showCV || showRL ? 'right-80' : 'right-0'
                } ${showRL ? 'bg-white/60 dark:bg-[#1E293B]/15 text-primary backdrop-blur-3xl' : 'bg-edu-surface-light dark:bg-[#1E293B]/40 text-primary/70 hover:text-primary hover:bg-edu-bg-light dark:hover:bg-[#1E293B]/60 backdrop-blur'
                }`}
            >
              <div className="flex flex-col items-center gap-4">
                {showRL ? <ChevronRight size={16} /> : <Bot size={18} />}
                <span className="text-[10px] font-black uppercase tracking-[0.2em] [writing-mode:vertical-lr] rotate-180">
                  {showRL ? 'Close' : 'RL Input'}
                </span>
              </div>
            </button>

          </div>
        );

      default:
        return <div>Unknown View</div>;
    }
  };

  return (
    <ThemeProvider>
      <div className="flex flex-col h-screen w-screen bg-edu-bg-light dark:bg-edu-bg-dark text-edu-text-light dark:text-edu-text-dark transition-colors duration-300 overflow-hidden font-sans">
        {/* Global Live CV Monitor - Survives sub-component crashes */}
        <LiveAffectSensing
          key={view === 'lesson' ? `cv-${currentTopicContext?.id || 'active'}` : 'cv-idle'}
          userId="alex_123"
          materialId={currentTopicContext?.title || "generic_topic"}
          interactionId={outcome?.meta?.interaction_id}
          enabled={view === 'lesson'}
        />

        {/* Global Navbar - Elevated Z-Index */}
        <div className="z-[100] relative">
          <Navbar currentView={view} onViewChange={setView} />
        </div>

        {/* Spacer ensures Navbar is cleared globally across all pages */}
        <div className="h-[110px] w-full shrink-0" />

        {/* Main Content Area */}
        <div className="flex-1 overflow-hidden relative">
          <AnimatePresence mode="wait">
            <motion.div
              key={view}
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.3, ease: "easeInOut" }}
              className="h-full w-full"
            >
              {renderContent()}
            </motion.div>
          </AnimatePresence>
        </div>
      </div>
    </ThemeProvider>
  );
}

export default App;
