import { supabase } from '../lib/supabase';
import type { Tables } from '../types/database';
import { toApiError } from './errors';

export type School = Tables<'schools'>;

/**
 * Every campus the app is open to. Readable without a session — the auth
 * screen needs this before the user has one.
 */
export async function listSchools(): Promise<School[]> {
  const { data, error } = await supabase
    .from('schools')
    .select('*')
    .order('name');

  if (error) {
    throw toApiError(error, 'Could not load the list of campuses.');
  }

  return data ?? [];
}

export function domainOf(email: string): string {
  return email.trim().toLowerCase().split('@')[1] ?? '';
}

/**
 * Resolve an email address to its campus, or null if the domain is not on the
 * allowlist. The signup trigger enforces the same rule server-side; this only
 * exists so the auth screen can say so before sending a pointless magic link.
 */
export async function findSchoolForEmail(email: string): Promise<School | null> {
  const domain = domainOf(email);
  if (!domain) return null;

  const { data, error } = await supabase
    .from('schools')
    .select('*')
    .eq('email_domain', domain)
    .maybeSingle();

  if (error) {
    throw toApiError(error, 'Could not check that email address.');
  }

  return data;
}
