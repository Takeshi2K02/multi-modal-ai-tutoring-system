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
import AgentDebugger from './pages/AgentDebugger';
import LearningLayout from './components/LearningLayout';
import LiveAffectSensing from './components/LiveAffectSensing';
import { ThemeProvider } from './context/ThemeContext';
import { AuthProvider, useAuth } from "./AuthContext";
import LoginPage from "./LoginPage";
import { Toaster, toast } from 'react-hot-toast';

// Initialize socket without autoConnect to prevent premature connection attempts (Project ID: 25-26J-130)
const socket = io('http://localhost:8000', {
  auth: { token: localStorage.getItem("token") },
  transports: ["websocket"],
  autoConnect: false,
});

function AppInner() {
  const { token, userId } = useAuth();
  const [view, setView] = useState('login'); 
  const [activeSessionId, setActiveSessionId] = useState(null);
  const [currentTopicContext, setCurrentTopicContext] = useState(null);
  const [isLessonReady, setIsLessonReady] = useState(false);
  const [contentGenRequest, setContentGenRequest] = useState(null); // New State
  const [countdown, setCountdown] = useState(0); // New State
  const [preGeneratedContent, setPreGeneratedContent] = useState(null); // PHASE 4: Direct Handoff
  const [currentCollectionId, setCurrentCollectionId] = useState(null);
  
  // Manage Socket Connection (Project ID: 25-26J-130)
  useEffect(() => {
    if (token) {
      socket.auth.token = token;
      socket.connect();
      console.log(">>> [Pipeline] Socket connecting with token...");
    } else {
      socket.disconnect();
      console.log(">>> [Pipeline] Socket disconnected (no token)");
    }
  }, [token]);

  // Dynamic Title
  useEffect(() => {
    const titles = {
      decomposition: 'EduSynth - Plan',
      curriculum: 'EduSynth - Curriculum',
      lesson: 'EduSynth - Lesson',
      dashboard: 'EduSynth - My Learning',
      upload: 'EduSynth - Upload',
      monitor: 'EduSynth - Admin Monitor',
      data: 'EduSynth - Data Center',
      agent: 'EduSynth - Agent Debugger',
      login: 'EduSynth - Login'
    };
    document.title = titles[view] || 'EduSynth AI Tutor';
  }, [view]);

  // Agent Core Reachability Check
  useEffect(() => {
    const checkCore = async () => {
      try {
        const res = await fetch(`${API_BASE_URL}/health`);
        if (res.ok) {
          console.log(">>> [Pipeline] Agentic Core on port 8000 is REACHABLE");
        } else {
          console.warn(">>> [Pipeline] Agentic Core returned non-OK status");
        }
      } catch (err) {
        console.error(">>> [Pipeline] Agentic Core is UNREACHABLE", err);
        toast.error("Agentic Core is unreachable. Check if the backend is running.", { duration: 5000 });
      }
    };
    if (token) checkCore();
  }, [token]);

  // Auth Redirect Logic
  useEffect(() => {
    if (token && view === 'login') {
      setView('decomposition');
    } else if (!token && view !== 'login') {
      setView('login');
    }
  }, [token, view]);

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

  // 1. Analytics Data Hooks (Conditional fetching: SWR won't fetch if token/userId are missing)
  const { data: analytics } = useSWR(token && userId ? `${API_BASE_URL}/api/analytics/historical?user_id=${userId}` : null, fetcher);
  const { data: latest } = useSWR(token && userId ? `${API_BASE_URL}/api/analytics/latest?user_id=${userId}` : null, fetcher, { refreshInterval: 2000 });

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
        console.log(">>> [Pipeline] Triggering handleRun with state:", randomPersona.state);
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

    const toastId = toast.loading("Fetching your content...", {
      style: {
        borderRadius: '16px',
        background: '#1e293b',
        color: '#fff',
        border: '1px solid rgba(255,255,255,0.1)'
      }
    });

    // Generate Synthesis ID for the session (Project ID: 25-26J-130)
    const synthesisId = `syn-${Date.now()}`;
    setOutcome({ meta: { interaction_id: synthesisId } }); // Optimistic state for listeners

    try {
      // Redirect removed to prevent jumping out of current context (Issue Fix)
      
      toast.loading("Analyzing topic chunks...", { id: toastId });

      const { runSimulation } = await import('./services/api');
      // Pass the current topic context, synthesis_id, and collectionId (Phase 21)
      const result = await runSimulation(
        scenario,
        currentTopicContext,
        synthesisId,
        currentTopicContext?.collectionId
      );

      toast.loading("Preparing your lesson...", { id: toastId });
      
      setGraphData(result);
      setOutcome(result);

      toast.success("Lesson synthesized successfully!", { id: toastId });

      // NOTE: Simulation complete, but we wait for VISUAL playback to finish before countdown.
    } catch (err) {
      console.error(err);
      const msg = err.response?.data?.detail || err.message || "Failed to connect to Agent backend.";
      setError(msg);
      toast.error(`Synthesis Failed: ${msg}`, { id: toastId });
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
      // Countdown finished, navigate to lesson view (Project ID: 25-26J-130)
      setView('lesson');
    }
  }, [countdown, contentGenRequest, view]);


  // --- Views ---

  const renderContent = () => {
    switch (view) {
      case 'decomposition':
        return (
          <GoalDecomposition
            collectionId={currentCollectionId}
            onBack={() => setView('upload')} // Navigates back to Upload instead of Agent Debugger
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
            onContinue={(topic, result) => {
              setCurrentTopicContext(topic);
              if (result) {
                setPreGeneratedContent(result);
                setIsLessonReady(true);
              } else {
                setIsLessonReady(false); // Reset for next lesson
                setPreGeneratedContent(null); // Clear old content
              }
              setView('lesson'); // Always navigate to lesson (Issue Fix)
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
            preGeneratedContent={preGeneratedContent} // PHASE 4
            onBack={() => {
              setIsLessonReady(false);
              setPreGeneratedContent(null);
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
            onSuccess={(cid) => {
              setCurrentCollectionId(cid);
              setView('decomposition');
            }}
          />
        );

      case 'monitor':
        return <AdminMonitor />;

      case 'data':
        return <DataDashboard />;

      case 'agent':
        return (
          <AgentDebugger
            context={{
              profile: demoPersona || { name: "Alex", preferred_modality: { visual: 0.33, textual: 0.33, interactive: 0.34 } },
              snapshot: latest?.cv || {},
              synthesis_id: outcome?.meta?.interaction_id
            }}
            onComplete={(payload) => {
              // PROJECT ID: 25-26J-130: Phase 4 Direct Handoff
              if (payload) {
                setPreGeneratedContent(payload);
              }
              setView('lesson');
            }}
          />
        );
      case 'login':
        return <LoginPage />;
      default:
        return <div>Unknown View</div>;
    }
  };

  const isAuthPage = view === 'login';

  return (
    <div className="flex flex-col h-screen w-screen bg-edu-bg-light dark:bg-edu-bg-dark text-edu-text-light dark:text-edu-text-dark transition-colors duration-300 overflow-hidden font-sans">
      {/* Global Live CV Monitor - Survives sub-component crashes */}
      {!isAuthPage && (
        <LiveAffectSensing
          key={view === 'lesson' ? `cv-${currentTopicContext?.id || 'active'}` : 'cv-idle'}
          userId={userId}
          materialId={currentTopicContext?.title || "generic_topic"}
          interactionId={outcome?.meta?.interaction_id}
          enabled={view === 'lesson'}
        />
      )}

      {/* Global Navbar - Elevated Z-Index */}
      {!isAuthPage && (
        <div className="z-[100] relative">
          <Navbar currentView={view} onViewChange={setView} />
        </div>
      )}

      {/* Spacer ensures Navbar is cleared globally across all pages */}
      {!isAuthPage && <div className="h-[110px] w-full shrink-0" />}

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
      <Toaster position="bottom-right" reverseOrder={false} />
    </div>
  );
}

export default function App() {
  return (
    <ThemeProvider>
      <AuthProvider>
        <AppInner />
      </AuthProvider>
    </ThemeProvider>
  );
}
