import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import GoalDecomposition from '../pages/GoalDecomposition';
import CurriculumBrowser from '../pages/CurriculumBrowser';
import LessonView from '../pages/LessonView';
import SessionDashboard from '../pages/SessionDashboard';
import LectureUpload from '../pages/LectureUpload';
import LoginPage from '../LoginPage';

export const AppRouter = ({ 
  view, 
  setView, 
  activeSessionId, 
  setActiveSessionId,
  currentTopicContext,
  setCurrentTopicContext,
  currentCollectionId,
  setCurrentCollectionId,
  setIsLessonReady,
  outcome,
  setOutcome,
  socket,
  latest,
  prefetchingTopic,
  setPrefetchingTopic,
  readyTopics,
  setReadyTopics
}) => {
  const renderContent = () => {
    switch (view) {
      case 'decomposition':
        return (
          <GoalDecomposition
            collectionId={currentCollectionId}
            onBack={() => setView('upload')}
            onStart={(sessionId) => {
              setActiveSessionId(sessionId);
              setView('dashboard');
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
              setIsLessonReady(false);
              setView('lesson');
            }}
            prefetchingTopic={prefetchingTopic}
            setPrefetchingTopic={setPrefetchingTopic}
            readyTopics={readyTopics}
            setReadyTopics={setReadyTopics}
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
            onPrefetchStarted={(title) => setPrefetchingTopic(title)}
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

      case 'login':
        return <LoginPage />;
      default:
        return <div>Unknown View</div>;
    }
  };

  return (
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
  );
};
