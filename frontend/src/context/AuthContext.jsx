import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import { SUPABASE_CONFIG_HINT } from "../lib/supabaseEnv.js";
import { supabase } from "../services/supabase.js";

const AuthContext = createContext(null);

function syncRealtimeAuth(accessToken) {
  if (!supabase) return;
  supabase.realtime.setAuth(accessToken ?? null);
}

export function AuthProvider({ children }) {
  const [session, setSession] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!supabase) {
      setLoading(false);
      return undefined;
    }

    supabase.auth.getSession().then(({ data }) => {
      const s = data.session ?? null;
      setSession(s);
      syncRealtimeAuth(s?.access_token);
      if (s?.access_token) {
        localStorage.setItem("sb-access-token", s.access_token);
      }
      setLoading(false);
    });

    const { data: sub } = supabase.auth.onAuthStateChange((_event, next) => {
      setSession(next);
      syncRealtimeAuth(next?.access_token);
      if (next?.access_token) {
        localStorage.setItem("sb-access-token", next.access_token);
      } else {
        localStorage.removeItem("sb-access-token");
      }
    });

    return () => sub.subscription.unsubscribe();
  }, []);

  const signIn = useCallback(async (email, password) => {
    if (!supabase) throw new Error(`Supabase is not configured. ${SUPABASE_CONFIG_HINT}`);
    const { data, error } = await supabase.auth.signInWithPassword({ email, password });
    if (error) throw error;
    return data;
  }, []);

  const signUp = useCallback(async (email, password, displayName) => {
    if (!supabase) throw new Error(`Supabase is not configured. ${SUPABASE_CONFIG_HINT}`);
    const { data, error } = await supabase.auth.signUp({
      email,
      password,
      options: {
        data: { display_name: displayName || email.split("@")[0] },
      },
    });
    if (error) throw error;
    return data;
  }, []);

  const registerAndSignIn = useCallback(async (email, password, displayName) => {
    if (!supabase) throw new Error(`Supabase is not configured. ${SUPABASE_CONFIG_HINT}`);

    // Register account first.
    const { error: signUpError } = await supabase.auth.signUp({
      email,
      password,
      options: {
        data: { display_name: displayName || email.split("@")[0] },
      },
    });
    if (signUpError) throw signUpError;

    // Then immediately try sign-in so user can continue without email flow.
    const { data: signInData, error: signInError } = await supabase.auth.signInWithPassword({
      email,
      password,
    });
    if (!signInError) return signInData;

    // If this happens, Supabase project still requires email confirmation.
    throw new Error(
      "Account created, but your Supabase project still requires email confirmation. " +
        "Disable 'Confirm email' in Supabase Auth > Providers > Email to enable direct sign-in.",
    );
  }, []);

  const signOut = useCallback(async () => {
    if (supabase) await supabase.auth.signOut();
    syncRealtimeAuth(null);
    localStorage.removeItem("sb-access-token");
    setSession(null);
  }, []);

  const value = useMemo(
    () => ({
      session,
      user: session?.user ?? null,
      loading,
      signIn,
      signUp,
      registerAndSignIn,
      signOut,
      isAuthenticated: !!session,
    }),
    [session, loading, signIn, signUp, registerAndSignIn, signOut],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
