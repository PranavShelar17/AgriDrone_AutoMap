"use client";

import React, { useState, useEffect, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { useAuth } from "@/lib/auth";
import { Sprout, Lock, Mail, AlertCircle, ArrowRight, Loader2, ShieldCheck, CheckCircle2 } from "lucide-react";

function LoginForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { login, isAuthenticated, user, isLoading: authLoading } = useAuth();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Safe redirect path validation (anti-open redirect)
  const getSafeReturnUrl = (rawUrl: string | null, role?: string): string => {
    if (!rawUrl || !rawUrl.startsWith("/") || rawUrl.startsWith("//") || rawUrl.includes("://")) {
      return role === "FARMER" ? "/portal/surveys" : "/admin/dashboard";
    }
    return rawUrl;
  };

  // If already logged in, redirect automatically
  useEffect(() => {
    if (!authLoading && isAuthenticated && user) {
      const returnUrl = getSafeReturnUrl(searchParams.get("returnUrl"), user.role);
      router.replace(returnUrl);
    }
  }, [authLoading, isAuthenticated, user, router, searchParams]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (isSubmitting) return;

    setErrorMessage(null);
    if (!email.trim() || !password) {
      setErrorMessage("Please enter both your email address and password.");
      return;
    }

    setIsSubmitting(true);
    try {
      const loggedUser = await login(email.trim(), password);
      const destination = getSafeReturnUrl(searchParams.get("returnUrl"), loggedUser.role);
      router.push(destination);
    } catch (err: any) {
      setErrorMessage(err?.message || "Invalid email or password. Please try again.");
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleFillDemo = (demoEmail: string, demoPass: string) => {
    setEmail(demoEmail);
    setPassword(demoPass);
    setErrorMessage(null);
  };

  return (
    <div className="min-h-[calc(100vh-8rem)] flex items-center justify-center px-4 py-12 sm:px-6 lg:px-8 bg-slate-50">
      <div className="w-full max-w-md space-y-8">
        {/* Header Branding */}
        <div className="text-center">
          <div className="mx-auto w-14 h-14 rounded-2xl bg-emerald-600 text-white flex items-center justify-center shadow-md">
            <Sprout className="w-8 h-8" />
          </div>
          <h1 className="mt-4 text-2xl font-bold tracking-tight text-slate-900 sm:text-3xl">
            AgriDrone AutoMap
          </h1>
          <p className="mt-2 text-sm text-slate-600">
            Sign in to access your farm maps, photogrammetry, and analytics
          </p>
        </div>

        {/* Login Card */}
        <div className="bg-white py-8 px-6 shadow-sm rounded-xl border border-slate-200 sm:px-8">
          <form className="space-y-6" onSubmit={handleSubmit} noValidate>
            {/* Error Announcement */}
            {errorMessage && (
              <div
                role="alert"
                aria-live="assertive"
                className="flex items-start gap-3 p-3.5 rounded-lg bg-rose-50 border border-rose-200 text-rose-800 text-sm"
              >
                <AlertCircle className="w-5 h-5 text-rose-600 shrink-0 mt-0.5" />
                <span className="font-medium">{errorMessage}</span>
              </div>
            )}

            {/* Email Field */}
            <div>
              <label
                htmlFor="email"
                className="block text-xs font-semibold uppercase tracking-wider text-slate-700 mb-1.5"
              >
                Email Address
              </label>
              <div className="relative rounded-lg shadow-2xs">
                <div className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3">
                  <Mail className="h-4 w-4 text-slate-400" aria-hidden="true" />
                </div>
                <input
                  id="email"
                  name="email"
                  type="email"
                  autoComplete="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  disabled={isSubmitting}
                  placeholder="farmer@example.com"
                  className="block w-full rounded-lg border border-slate-300 pl-10 pr-3 py-2.5 text-sm text-slate-900 placeholder:text-slate-400 focus:border-emerald-600 focus:outline-none focus:ring-1 focus:ring-emerald-600 disabled:bg-slate-50 disabled:text-slate-500"
                />
              </div>
            </div>

            {/* Password Field */}
            <div>
              <label
                htmlFor="password"
                className="block text-xs font-semibold uppercase tracking-wider text-slate-700 mb-1.5"
              >
                Password
              </label>
              <div className="relative rounded-lg shadow-2xs">
                <div className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3">
                  <Lock className="h-4 w-4 text-slate-400" aria-hidden="true" />
                </div>
                <input
                  id="password"
                  name="password"
                  type="password"
                  autoComplete="current-password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  disabled={isSubmitting}
                  placeholder="••••••••••••"
                  className="block w-full rounded-lg border border-slate-300 pl-10 pr-3 py-2.5 text-sm text-slate-900 placeholder:text-slate-400 focus:border-emerald-600 focus:outline-none focus:ring-1 focus:ring-emerald-600 disabled:bg-slate-50 disabled:text-slate-500"
                />
              </div>
            </div>

            {/* Submit Button */}
            <div>
              <button
                type="submit"
                disabled={isSubmitting}
                className="w-full flex items-center justify-center gap-2 py-2.5 px-4 rounded-lg text-sm font-semibold text-white bg-emerald-600 hover:bg-emerald-700 active:bg-emerald-800 shadow-xs focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:ring-offset-2 transition-colors disabled:opacity-60 disabled:cursor-not-allowed"
              >
                {isSubmitting ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    <span>Signing In...</span>
                  </>
                ) : (
                  <>
                    <span>Sign In</span>
                    <ArrowRight className="w-4 h-4" />
                  </>
                )}
              </button>
            </div>
          </form>

          {/* Quick Demo Accounts for Testing */}
          <div className="mt-8 pt-6 border-t border-slate-200">
            <div className="flex items-center gap-2 mb-3">
              <ShieldCheck className="w-4 h-4 text-emerald-600" />
              <span className="text-xs font-semibold text-slate-700 uppercase tracking-wider">
                Evaluation Test Credentials
              </span>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs">
              <button
                type="button"
                onClick={() => handleFillDemo("admin@agridrone.local", "Admin@AgriDrone2026!")}
                className="flex items-center justify-between p-2.5 rounded-lg border border-slate-200 hover:border-emerald-300 hover:bg-emerald-50/50 text-left transition-colors"
              >
                <div>
                  <span className="font-semibold text-slate-800 block">Admin Operator</span>
                  <span className="text-[11px] text-slate-500">Full Platform Access</span>
                </div>
                <CheckCircle2 className="w-3.5 h-3.5 text-slate-400" />
              </button>

              <button
                type="button"
                onClick={() => handleFillDemo("farmer@greenvalley.local", "Farmer@AgriDrone2026!")}
                className="flex items-center justify-between p-2.5 rounded-lg border border-slate-200 hover:border-emerald-300 hover:bg-emerald-50/50 text-left transition-colors"
              >
                <div>
                  <span className="font-semibold text-slate-800 block">Farmer (Baramati)</span>
                  <span className="text-[11px] text-slate-500">Isolated Farm Access</span>
                </div>
                <CheckCircle2 className="w-3.5 h-3.5 text-slate-400" />
              </button>
            </div>
          </div>
        </div>

        {/* Security Notice */}
        <p className="text-center text-xs text-slate-500">
          Protected by role-based authorization & resource-level isolation.
        </p>
      </div>
    </div>
  );
}

export default function LoginPage() {
  return (
    <Suspense
      fallback={
        <div className="min-h-[calc(100vh-8rem)] flex items-center justify-center bg-slate-50">
          <div className="flex items-center gap-2 text-sm text-slate-500">
            <Loader2 className="w-5 h-5 animate-spin text-emerald-600" />
            <span>Loading authentication portal...</span>
          </div>
        </div>
      }
    >
      <LoginForm />
    </Suspense>
  );
}
