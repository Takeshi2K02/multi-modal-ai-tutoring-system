import React from 'react';
import useSWR from 'swr';
import { fetcher, API_BASE_URL } from './services/api';
import { useAppBootstrap } from './core/useAppBootstrap';
import { useAuthGuard } from './core/useAuthGuard';
import { AppProviders } from './core/AppProviders';
import { AppRouter } from './core/AppRouter';
import { GlobalOverlays } from './core/GlobalOverlays';

function AppInner() {
  const bootstrap = useAppBootstrap();
  useAuthGuard(bootstrap.token, bootstrap.view, bootstrap.setView);

  // Analytics Data Hooks (Requirement: Survives sub-component crashes)
  const { data: latest } = useSWR(
    bootstrap.token && bootstrap.userId 
      ? `${API_BASE_URL}/api/analytics/latest?user_id=${bootstrap.userId}` 
      : null, 
    fetcher, 
    { refreshInterval: 2000 }
  );

  return (
    <div className="flex flex-col h-screen w-screen bg-edu-bg-light dark:bg-edu-bg-dark text-edu-text-light dark:text-edu-text-dark transition-colors duration-300 overflow-hidden font-sans">
      <GlobalOverlays 
        view={bootstrap.view} 
        setView={bootstrap.setView}
        userId={bootstrap.userId}
        currentTopicContext={bootstrap.currentTopicContext}
        outcome={bootstrap.outcome}
      />
      
      <AppRouter 
        {...bootstrap}
        latest={latest}
      />
    </div>
  );
}

export default function App() {
  return (
    <AppProviders>
      <AppInner />
    </AppProviders>
  );
}
