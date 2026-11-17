
import { createContext, useContext, useState } from "react";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(null);

  // Temporary frontend-only demo login.
  // Replace with FastAPI authentication later.
  async function login(email, password) {
    if (!email || !password) {
      throw new Error("Email and password are required.");
    }

    const demoUser = {
      id: "DEMO-ASHA-001",
      name: "ASHA Worker",
      email,
      role: "asha",
      authMode: "demo"
    };

    const demoToken = "DEMO_TOKEN_NOT_FOR_PRODUCTION";

    setUser(demoUser);
    setToken(demoToken);

    return demoUser;
  }

  function logout() {
    setUser(null);
    setToken(null);
  }

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        isAuthenticated: Boolean(user && token),
        login,
        logout
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);

  if (!context) {
    throw new Error("useAuth must be used inside AuthProvider.");
  }

  return context;
}
