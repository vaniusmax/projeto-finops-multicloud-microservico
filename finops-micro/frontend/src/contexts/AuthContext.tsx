"use client";

import { createContext, useContext, useEffect, useState } from "react";

import { getMe, postLogin, postLogout, postRegister, postVerifyEmail, type LoginPayload, type RegisterPayload, type VerifyEmailPayload } from "@/lib/api/auth";
import { clearStoredAccessToken, getStoredAccessToken, setStoredAccessToken } from "@/lib/auth/storage";
import type { AuthRegisterResponse, AuthUser } from "@/lib/schemas/auth";

type AuthContextValue = {
  user: AuthUser | null;
  isAuthenticated: boolean;
  isReady: boolean;
  login: (payload: LoginPayload) => Promise<void>;
  register: (payload: RegisterPayload) => Promise<AuthRegisterResponse>;
  verifyEmail: (payload: VerifyEmailPayload) => Promise<void>;
  logout: () => Promise<void>;
};

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [isReady, setIsReady] = useState(false);

  useEffect(() => {
    const token = getStoredAccessToken();
    if (!token) {
      setIsReady(true);
      return;
    }

    void getMe()
      .then((me) => setUser(me))
      .catch(() => {
        clearStoredAccessToken();
        setUser(null);
      })
      .finally(() => setIsReady(true));
  }, []);

  async function login(payload: LoginPayload) {
    const session = await postLogin(payload);
    setStoredAccessToken(session.accessToken);
    setUser(session.user);
  }

  async function register(payload: RegisterPayload) {
    return postRegister(payload);
  }

  async function verifyEmail(payload: VerifyEmailPayload) {
    const session = await postVerifyEmail(payload);
    setStoredAccessToken(session.accessToken);
    setUser(session.user);
  }

  async function logout() {
    try {
      await postLogout();
    } finally {
      clearStoredAccessToken();
      setUser(null);
    }
  }

  return (
    <AuthContext.Provider
      value={{
        user,
        isAuthenticated: !!user,
        isReady,
        login,
        register,
        verifyEmail,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within AuthProvider");
  }
  return context;
}
