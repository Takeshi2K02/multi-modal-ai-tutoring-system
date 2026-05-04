import { io } from 'socket.io-client';

// Hardened Singleton Pattern (Project ID: 25-26J-130)
// Prevents multiple socket instances during Vite HMR or component remounts.
const getSocket = () => {
  if (typeof window === 'undefined') return null;
  
  if (!window.__EDUSYNTH_SOCKET__) {
    if (import.meta.env.DEV) {
      console.log(">>> [Pipeline] Creating Global Socket Instance");
    }
    window.__EDUSYNTH_SOCKET__ = io('http://localhost:8000', {
      auth: { token: null },
      transports: ["websocket"],
      autoConnect: false,
      reconnection: true,
      reconnectionAttempts: 10,
      reconnectionDelay: 1000,
    });

    window.__EDUSYNTH_SOCKET__.__CONNECTING__ = false;

    window.__EDUSYNTH_SOCKET__.on('connect', () => {
      window.__EDUSYNTH_SOCKET__.__CONNECTING__ = false;
      if (import.meta.env.DEV) console.log(">>> [Pipeline] Socket Connected:", window.__EDUSYNTH_SOCKET__.id);
    });

    window.__EDUSYNTH_SOCKET__.on('connect_error', () => {
      window.__EDUSYNTH_SOCKET__.__CONNECTING__ = false;
      if (import.meta.env.DEV) console.error(">>> [Pipeline] Socket Connection Error");
    });
  }
  return window.__EDUSYNTH_SOCKET__;
};

export const socket = getSocket();

// Optional: HMR Disposal is now safer as we use a global
if (import.meta.hot) {
  import.meta.hot.dispose(() => {
    // We don't disconnect here to maintain persistent state across HMR
    // console.log(">>> [Pipeline] HMR Disposal - Keeping socket alive");
  });
}
