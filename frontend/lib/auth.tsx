"use client";

import React, { createContext, useContext, useEffect, useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import { api, UserProfile, ApiClientError } from "./api";

interface AuthContextType {
  user: UserProfile | null;
  token: string | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  isAdmin: boolean;
  isFarmer: boolean;
  login: (email: string, password: string) => Promise<UserProfile>;
  logout: () => Promise<void>;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<UserProfile | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const router = useRouter();

  // Load session from localStorage on mount
  useEffect(() => {
    let isMounted = true;

    async function initAuth() {
      try {
        if (typeof window !== "undefined") {
          const storedToken = localStorage.getItem("agridrone_token");
          const storedUserJson = localStorage.getItem("agridrone_user");

          if (storedToken) {
            setToken(storedToken);
            if (storedUserJson) {
              try {
                setUser(JSON.parse(storedUserJson));
              } catch {
                // Ignore parse errors, will refresh via api.auth.getMe()
              }
            }

            // Validate token & fresh user state with backend
            try {
              const freshUser = await api.auth.getMe();
              if (isMounted) {
                setUser(freshUser);
              }
            } catch (err) {
              if (err instanceof ApiClientError && err.status === 401) {
                if (isMounted) {
                  setUser(null);
                  setToken(null);
                }
              }
            }
          }
        }
      } catch (err) {
        console.error("Failed to initialize authentication state:", err);
      } finally {
        if (isMounted) {
          setIsLoading(false);
        }
      }
    }

    initAuth();

    return () => {
      isMounted = false;
    };
  }, []);

  const login = useCallback(
    async (email: string, password: string): Promise<UserProfile> => {
      setIsLoading(true);
      try {
        const res = await api.auth.login(email, password);
        setToken(res.access_token);
        setUser(res.user);
        return res.user;
      } finally {
        setIsLoading(false);
      }
    },
    []
  );

  const logout = useCallback(async () => {
    setIsLoading(true);
    try {
      await api.auth.logout();
    } finally {
      setUser(null);
      setToken(null);
      setIsLoading(false);
      router.push("/login");
    }
  }, [router]);

  const refreshUser = useCallback(async () => {
    try {
      const freshUser = await api.auth.getMe();
      setUser(freshUser);
    } catch {
      // Invalidation handled by api.auth.getMe()
    }
  }, []);

  const value: AuthContextType = {
    user,
    token,
    isLoading,
    isAuthenticated: !!user && !!token,
    isAdmin: user?.role === "ADMIN",
    isFarmer: user?.role === "FARMER",
    login,
    logout,
    refreshUser,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextType {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
