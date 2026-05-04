import { useState, useEffect } from 'react';
import { socket } from '../services/socket';
import { API_BASE_URL } from '../services/api';
import { toast } from 'react-hot-toast';
import { useAuth } from '../AuthContext';

export const useAppBootstrap = () => {
  const { token, userId } = useAuth();
  const [view, setView] = useState('login');
  const [isBackendReady, setIsBackendReady] = useState(false);
  const [activeSessionId, setActiveSessionId] = useState(null);
  const [currentTopicContext, setCurrentTopicContext] = useState(null);
  const [currentCollectionId, setCurrentCollectionId] = useState(null);
  const [isLessonReady, setIsLessonReady] = useState(false);
  const [outcome, setOutcome] = useState(null);
  const [prefetchingTopic, setPrefetchingTopic] = useState(null);
  const [readyTopics, setReadyTopics] = useState([]);

  // Manage Socket Connection
  useEffect(() => {
    if (token) {
      socket.auth.token = token;
      if (!socket.connected && !socket.__CONNECTING__) {
        socket.__CONNECTING__ = true;
        socket.connect();
        if (import.meta.env.DEV) console.log(">>> [Pipeline] Socket connecting with token...");
      }
    } else {
      if (socket.connected) {
        socket.disconnect();
        if (import.meta.env.DEV) console.log(">>> [Pipeline] Socket disconnected (no token)");
      }
    }
  }, [token]);

  // Agent Core Reachability Check
  useEffect(() => {
    const checkCore = async () => {
      try {
        const res = await fetch(`${API_BASE_URL}/health`);
        if (res.ok) {
          setIsBackendReady(true);
          if (import.meta.env.DEV) console.log(">>> [Pipeline] Agentic Core on port 8000 is REACHABLE");
        } else {
          setIsBackendReady(false);
          console.warn(">>> [Pipeline] Agentic Core returned non-OK status");
        }
      } catch (err) {
        setIsBackendReady(false);
        console.error(">>> [Pipeline] Agentic Core is UNREACHABLE", err);
        toast.error("Agentic Core is unreachable. Check if the backend is running.", { duration: 5000 });
      }
    };
    if (token) checkCore();
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

  return {
    socket,
    isBackendReady,
    view,
    setView,
    activeSessionId,
    setActiveSessionId,
    currentTopicContext,
    setCurrentTopicContext,
    currentCollectionId,
    setCurrentCollectionId,
    isLessonReady,
    setIsLessonReady,
    outcome,
    setOutcome,
    prefetchingTopic,
    setPrefetchingTopic,
    readyTopics,
    setReadyTopics,
    userId,
    token
  };
};
