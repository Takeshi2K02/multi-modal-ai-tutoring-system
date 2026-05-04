import React from 'react';
import { ThemeProvider } from '../context/ThemeContext';
import { AuthProvider } from '../AuthContext';
import { Toaster } from 'react-hot-toast';

export const AppProviders = ({ children }) => {
  return (
    <ThemeProvider>
      <AuthProvider>
        {children}
        <Toaster position="bottom-right" reverseOrder={false} />
      </AuthProvider>
    </ThemeProvider>
  );
};
