import React from 'react';
import Navbar from '../components/Navbar';
import LiveAffectSensing from '../components/LiveAffectSensing';

export const GlobalOverlays = ({ 
  view, 
  setView, 
  userId, 
  currentTopicContext, 
  outcome 
}) => {
  const isAuthPage = view === 'login';

  if (isAuthPage) return null;

  return (
    <>
      <div className="z-[100] relative">
        <Navbar currentView={view} onViewChange={setView} />
      </div>

      {/* Spacer ensures Navbar is cleared globally across all pages */}
      <div className="h-[110px] w-full shrink-0" />

      <LiveAffectSensing
        userId={userId}
        materialId={currentTopicContext?.title || "generic_topic"}
        interactionId={outcome?.meta?.interaction_id}
        enabled={view === 'lesson' || view === 'curriculum'}
      />
    </>
  );
};
