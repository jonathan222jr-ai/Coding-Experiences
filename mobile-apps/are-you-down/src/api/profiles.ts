import { supabase } from '../lib/supabase';
import type { Tables } from '../types/database';
import { toApiError } from './errors';
import type { School } from './schools';

export type Profile = Tables<'profiles'>;

export interface ProfileWithSchool extends Profile {
  school: School;
}

/** Someone else's profile, as shown on the person screen. */
export interface PublicProfile {
  id: string;
  display_name: string;
  avatar_url: string | null;
  bio: string | null;
  pronouns: string | null;
  major: string | null;
  class_year: string | null;
  interests: string[];
}

export const CLASS_YEARS = [
  { value: 'freshman', label: 'Freshman' },
  { value: 'sophomore', label: 'Sophomore' },
  { value: 'junior', label: 'Junior' },
  { value: 'senior', label: 'Senior' },
  { value: 'grad', label: 'Grad' },
  { value: 'other', label: 'Other' },
] as const;

export const BIO_MAX = 160;
export const MAJOR_MAX = 60;
export const PRONOUNS_MAX = 24;
export const MAX_INTERESTS = 6;

export function classYearLabel(value: string | null): string | null {
  return CLASS_YEARS.find((year) => year.value === value)?.label ?? null;
}

/**
 * The signed-in user's profile, with their campus joined in.
 *
 * Profiles are created by the signup trigger, so a missing row here means the
 * session outlived its user — the caller should treat that as signed out.
 */
export async function getMyProfile(userId: string): Promise<ProfileWithSchool | null> {
  const { data, error } = await supabase
    .from('profiles')
    .select(
      'id, school_id, display_name, avatar_url, bio, pronouns, major, class_year, created_at, school:schools(*)',
    )
    .eq('id', userId)
    .maybeSingle()
    .returns<ProfileWithSchool | null>();

  if (error) {
    throw toApiError(error, 'Could not load your profile.');
  }

  return data;
}

interface InterestRow {
  category_slug: string;
}

/**
 * Somebody else's profile. RLS restricts this to the caller's own campus, so
 * there is no cross-school lookup to guard against here.
 */
export async function fetchPublicProfile(userId: string): Promise<PublicProfile | null> {
  const [profileResult, interestResult] = await Promise.all([
    supabase
      .from('profiles')
      .select('id, display_name, avatar_url, bio, pronouns, major, class_year')
      .eq('id', userId)
      .maybeSingle()
      .returns<Omit<PublicProfile, 'interests'> | null>(),
    supabase
      .from('profile_interests')
      .select('category_slug')
      .eq('profile_id', userId)
      .returns<InterestRow[]>(),
  ]);

  if (profileResult.error) {
    throw toApiError(profileResult.error, 'Could not load that profile.');
  }

  if (!profileResult.data) return null;

  return {
    ...profileResult.data,
    interests: (interestResult.data ?? []).map((row) => row.category_slug),
  };
}

export interface ProfileChanges {
  display_name?: string;
  avatar_url?: string | null;
  bio?: string | null;
  pronouns?: string | null;
  major?: string | null;
  class_year?: string | null;
}

/** Empty strings mean "clear this", which the column stores as NULL. */
function blankToNull(value: string | null | undefined): string | null | undefined {
  if (value === undefined) return undefined;
  if (value === null) return null;
  const trimmed = value.trim();
  return trimmed.length === 0 ? null : trimmed;
}

export async function updateProfile(
  userId: string,
  changes: ProfileChanges,
): Promise<Profile> {
  const patch: ProfileChanges = {};

  if (changes.display_name !== undefined) patch.display_name = changes.display_name.trim();
  if (changes.avatar_url !== undefined) patch.avatar_url = changes.avatar_url;
  if (changes.bio !== undefined) patch.bio = blankToNull(changes.bio);
  if (changes.pronouns !== undefined) patch.pronouns = blankToNull(changes.pronouns);
  if (changes.major !== undefined) patch.major = blankToNull(changes.major);
  if (changes.class_year !== undefined) patch.class_year = changes.class_year;

  const { data, error } = await supabase
    .from('profiles')
    .update(patch)
    .eq('id', userId)
    .select()
    .single();

  if (error) {
    throw toApiError(error, 'Could not save your profile.');
  }

  return data;
}

export async function fetchMyInterests(userId: string): Promise<string[]> {
  const { data, error } = await supabase
    .from('profile_interests')
    .select('category_slug')
    .eq('profile_id', userId)
    .returns<InterestRow[]>();

  if (error) {
    throw toApiError(error, 'Could not load your interests.');
  }

  return (data ?? []).map((row) => row.category_slug);
}

/**
 * Add or remove a single interest.
 *
 * One row at a time rather than a replace-all diff: the six-interest cap is a
 * BEFORE INSERT trigger, so a bulk delete-then-insert would briefly empty the
 * set and lose it entirely if the insert half failed.
 */
export async function addInterest(userId: string, slug: string): Promise<void> {
  const { error } = await supabase
    .from('profile_interests')
    .insert({ profile_id: userId, category_slug: slug });

  if (error) {
    throw toApiError(error, 'Could not add that interest.');
  }
}

export async function removeInterest(userId: string, slug: string): Promise<void> {
  const { error } = await supabase
    .from('profile_interests')
    .delete()
    .eq('profile_id', userId)
    .eq('category_slug', slug);

  if (error) {
    throw toApiError(error, 'Could not remove that interest.');
  }
}
