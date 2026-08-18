import * as Linking from 'expo-linking';
import type { Session } from '@supabase/supabase-js';

import { supabase } from '../lib/supabase';
import { ApiError, toApiError } from './errors';
import { domainOf, findSchoolForEmail, type School } from './schools';

/**
 * Where the magic link sends the user back to. In Expo Go this resolves to an
 * exp:// URL, in a standalone build to areyoudown://.
 */
export const authRedirectUrl = Linking.createURL('auth-callback');

const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

export function normalizeEmail(email: string): string {
  return email.trim().toLowerCase();
}

/**
 * Send a sign-in link, but only to an address whose domain is a campus we
 * actually support.
 *
 * The check here is a courtesy: it lets the screen say "we don't cover that
 * campus yet" instead of silently sending a link that would fail on tap. The
 * real gate is the handle_new_user() trigger, which aborts the signup
 * transaction for an unknown domain no matter how the request arrives.
 */
export async function sendMagicLink(rawEmail: string): Promise<School> {
  const email = normalizeEmail(rawEmail);

  if (!EMAIL_PATTERN.test(email)) {
    throw new ApiError('That does not look like an email address.');
  }

  const school = await findSchoolForEmail(email);

  if (!school) {
    throw new ApiError(
      `@${domainOf(email)} isn't on the list yet. Use your school email address.`,
    );
  }

  const { error } = await supabase.auth.signInWithOtp({
    email,
    options: {
      emailRedirectTo: authRedirectUrl,
      shouldCreateUser: true,
    },
  });

  if (error) {
    throw toApiError(error, 'Could not send your sign-in link. Try again.');
  }

  return school;
}

/**
 * Fallback path for the six-digit code in the same email.
 *
 * Deep links back into Expo Go are unreliable enough that a code entry field
 * is worth the extra twenty lines.
 */
export async function verifyEmailCode(rawEmail: string, code: string): Promise<Session> {
  const email = normalizeEmail(rawEmail);
  const token = code.replace(/\D/g, '');

  if (token.length !== 6) {
    throw new ApiError('Enter the six-digit code from your email.');
  }

  const { data, error } = await supabase.auth.verifyOtp({
    email,
    token,
    type: 'email',
  });

  if (error || !data.session) {
    throw toApiError(error, 'That code is wrong or has expired.');
  }

  return data.session;
}

/**
 * Complete a sign-in from a deep link. Returns false when the URL is not an
 * auth callback, so the caller can ignore ordinary links.
 */
export async function completeSessionFromUrl(url: string): Promise<boolean> {
  const { queryParams } = Linking.parse(url);

  const errorDescription = queryParams?.error_description;
  if (typeof errorDescription === 'string') {
    throw new ApiError(errorDescription);
  }

  // PKCE: the link carries a one-time code we swap for a session using the
  // verifier this device stashed when it requested the link.
  const code = queryParams?.code;
  if (typeof code === 'string') {
    const { error } = await supabase.auth.exchangeCodeForSession(code);
    if (error) {
      throw toApiError(error, 'That sign-in link has expired. Request a new one.');
    }
    return true;
  }

  // Implicit flow, or a link opened on a device that didn't request it: the
  // tokens arrive in the URL fragment instead.
  const fragment = url.split('#')[1];
  if (fragment) {
    const params = new URLSearchParams(fragment);
    const accessToken = params.get('access_token');
    const refreshToken = params.get('refresh_token');

    if (accessToken && refreshToken) {
      const { error } = await supabase.auth.setSession({
        access_token: accessToken,
        refresh_token: refreshToken,
      });
      if (error) {
        throw toApiError(error, 'That sign-in link has expired. Request a new one.');
      }
      return true;
    }
  }

  return false;
}

export async function getSession(): Promise<Session | null> {
  const { data, error } = await supabase.auth.getSession();
  if (error) {
    throw toApiError(error, 'Could not restore your session.');
  }
  return data.session;
}

export async function signOut(): Promise<void> {
  const { error } = await supabase.auth.signOut();
  if (error) {
    throw toApiError(error, 'Could not sign out.');
  }
}
