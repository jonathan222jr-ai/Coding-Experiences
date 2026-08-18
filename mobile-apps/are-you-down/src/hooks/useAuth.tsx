import type { Session } from '@supabase/supabase-js';
import * as Linking from 'expo-linking';
import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
  type ReactNode,
} from 'react';

import { completeSessionFromUrl, signOut as signOutApi } from '../api/auth';
import { getMyProfile, type ProfileWithSchool } from '../api/profiles';
import { supabase } from '../lib/supabase';

type AuthStatus = 'loading' | 'signedOut' | 'signedIn';

interface AuthContextValue {
  status: AuthStatus;
  session: Session | null;
  profile: ProfileWithSchool | null;
  /** Set when a deep link failed to produce a session, so the auth screen can say why. */
  linkError: string | null;
  clearLinkError: () => void;
  /** Set when we hold a valid session but couldn't load the profile behind it. */
  profileError: string | null;
  refreshProfile: () => Promise<void>;
  signOut: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [status, setStatus] = useState<AuthStatus>('loading');
  const [session, setSession] = useState<Session | null>(null);
  const [profile, setProfile] = useState<ProfileWithSchool | null>(null);
  const [linkError, setLinkError] = useState<string | null>(null);
  const [profileError, setProfileError] = useState<string | null>(null);

  // Deep links can arrive before the session listener has settled; this keeps
  // us from racing two profile loads for the same user.
  const loadedForUser = useRef<string | null>(null);

  const loadProfile = useCallback(async (userId: string) => {
    try {
      const next = await getMyProfile(userId);

      if (!next) {
        // The user row is gone but the token is still valid locally. Drop it.
        await supabase.auth.signOut();
        return;
      }

      loadedForUser.current = userId;
      setProfile(next);
      setProfileError(null);
    } catch (error) {
      setProfileError(error instanceof Error ? error.message : String(error));
      throw error;
    }
  }, []);

  useEffect(() => {
    let active = true;

    void (async () => {
      const { data } = await supabase.auth.getSession();
      if (!active) return;

      setSession(data.session);

      if (data.session) {
        try {
          await loadProfile(data.session.user.id);
        } catch {
          // Offline on a cold start: keep the session, let the screen retry.
        }
      }

      if (active) {
        setStatus(data.session ? 'signedIn' : 'signedOut');
      }
    })();

    const { data: subscription } = supabase.auth.onAuthStateChange((_event, nextSession) => {
      setSession(nextSession);

      if (!nextSession) {
        loadedForUser.current = null;
        setProfile(null);
        setStatus('signedOut');
        return;
      }

      setStatus('signedIn');

      if (loadedForUser.current !== nextSession.user.id) {
        void loadProfile(nextSession.user.id).catch(() => {
          /* surfaced by the screen's own retry */
        });
      }
    });

    return () => {
      active = false;
      subscription.subscription.unsubscribe();
    };
  }, [loadProfile]);

  // Magic-link callbacks: one for a cold start, one for a link tapped while
  // the app is already open.
  useEffect(() => {
    let active = true;

    const handle = (url: string) => {
      completeSessionFromUrl(url).catch((error: unknown) => {
        if (!active) return;
        setLinkError(error instanceof Error ? error.message : String(error));
      });
    };

    void Linking.getInitialURL().then((url) => {
      if (url && active) handle(url);
    });

    const listener = Linking.addEventListener('url', ({ url }) => handle(url));

    return () => {
      active = false;
      listener.remove();
    };
  }, []);

  const refreshProfile = useCallback(async () => {
    if (session) {
      await loadProfile(session.user.id);
    }
  }, [loadProfile, session]);

  const signOut = useCallback(async () => {
    await signOutApi();
  }, []);

  const value = useMemo<AuthContextValue>(
    () => ({
      status,
      session,
      profile,
      linkError,
      clearLinkError: () => setLinkError(null),
      profileError,
      refreshProfile,
      signOut,
    }),
    [status, session, profile, linkError, profileError, refreshProfile, signOut],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used inside an AuthProvider.');
  }
  return context;
}

/**
 * For screens that only render behind a session. Throws rather than handing
 * back nullable values every caller would have to narrow.
 */
export function useCurrentUser(): { userId: string; profile: ProfileWithSchool } {
  const { session, profile } = useAuth();
  if (!session || !profile) {
    throw new Error('useCurrentUser must be used inside a signed-in screen.');
  }
  return { userId: session.user.id, profile };
}
