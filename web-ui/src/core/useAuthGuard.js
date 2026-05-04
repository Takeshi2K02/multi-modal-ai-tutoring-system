import { useEffect } from 'react';

export const useAuthGuard = (token, view, setView) => {
  useEffect(() => {
    if (token && view === 'login') {
      setView('decomposition');
    } else if (!token && view !== 'login') {
      setView('login');
    }
  }, [token, view, setView]);
};
