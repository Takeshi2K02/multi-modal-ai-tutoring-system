import { useState, useEffect } from 'react';
import { toast } from 'react-hot-toast';

export const useSimulation = (view, setView, currentTopicContext, setOutcome, outcome) => {
  const [graphData, setGraphData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [countdown, setCountdown] = useState(0);
  const [contentGenRequest, setContentGenRequest] = useState(null);
  const [demoPersona, setDemoPersona] = useState(null);
  const [isDemoMode, setIsDemoMode] = useState(false);

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

    const synthesisId = `syn-${Date.now()}`;
    setOutcome({ meta: { interaction_id: synthesisId } });

    try {
      toast.loading("Analyzing topic chunks...", { id: toastId });
      const { runSimulation } = await import('../services/api');
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
    if (countdown > 0) return;
    if (!outcome || !demoPersona) return;

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
      directive,
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
    setCountdown(10);
  };

  useEffect(() => {
    if (view === 'agent' && currentTopicContext) {
      setIsDemoMode(true);
      setCountdown(0);
      setContentGenRequest(null);

      const randomPersona = MOCK_PERSONAS[Math.floor(Math.random() * MOCK_PERSONAS.length)];
      setDemoPersona(randomPersona);

      const timer = setTimeout(() => {
        handleRun(randomPersona.state);
      }, 1000);

      return () => clearTimeout(timer);
    } else {
      setIsDemoMode(false);
    }
  }, [view, currentTopicContext]);

  useEffect(() => {
    if (countdown > 0) {
      const timer = setTimeout(() => setCountdown(c => c - 1), 1000);
      return () => clearTimeout(timer);
    } else if (countdown === 0 && contentGenRequest && view === 'agent') {
      setView('lesson');
    }
  }, [countdown, contentGenRequest, view]);

  return {
    graphData,
    loading,
    error,
    countdown,
    demoPersona,
    handleSimulationComplete
  };
};
