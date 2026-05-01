import { createContext, useContext, useState } from "react";

const AuthContext = createContext(null);
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

export function AuthProvider({ children }) {
  const [token, setToken] = useState(() => localStorage.getItem("token"));
  const [userId, setUserId] = useState(() => localStorage.getItem("userId"));

  async function login(email, password) {
    const res = await fetch(`${API_BASE_URL}/api/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
    });
    if (!res.ok) throw new Error("Login failed. Check your email and password.");
    const data = await res.json();
    localStorage.setItem("token", data.access_token);
    localStorage.setItem("userId", data.user_id);
    setToken(data.access_token);
    setUserId(data.user_id);
  }

  async function register(registrationData) {
    const res = await fetch(`${API_BASE_URL}/api/auth/register`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(registrationData),
    });
    if (!res.ok) {
      const errorData = await res.json();
      throw new Error(errorData.detail || "Registration failed");
    }
    // Success - user will be informed by the LoginPage and asked to log in manually
  }

  function logout() {
    localStorage.removeItem("token");
    localStorage.removeItem("userId");
    setToken(null);
    setUserId(null);
  }

  return (
    <AuthContext.Provider value={{ token, userId, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}
