import 'react-native-url-polyfill/auto';

import AsyncStorage from '@react-native-async-storage/async-storage';
import { createClient } from '@supabase/supabase-js';
import { AppState } from 'react-native';

import type { Database } from '../types/database';
import { env } from './env';

export const supabase = createClient<Database>(env.supabaseUrl, env.supabaseAnonKey, {
  auth: {
    storage: AsyncStorage,
    autoRefreshToken: true,
    persistSession: true,
    // React Native has no URL bar for Supabase to parse a session out of; the
    // auth provider handles the magic-link deep link itself.
    detectSessionInUrl: false,
    // PKCE keeps the token exchange off the redirect URL, which matters on
    // mobile where any app can register a custom scheme.
    flowType: 'pkce',
  },
});

// supabase-js schedules token refreshes with setInterval, which iOS and Android
// suspend in the background. Tie the refresh loop to foreground state so a
// session that was asleep for an hour comes back valid instead of 401-ing.
AppState.addEventListener('change', (state) => {
  if (state === 'active') {
    void supabase.auth.startAutoRefresh();
  } else {
    void supabase.auth.stopAutoRefresh();
  }
});
