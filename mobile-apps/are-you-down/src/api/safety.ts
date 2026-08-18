import { supabase } from '../lib/supabase';
import type { ReportTarget } from '../types/database';
import { toApiError } from './errors';

export interface BlockedUser {
  user_id: string;
  display_name: string;
  avatar_url: string | null;
  blocked_at: string;
}

interface BlockRow {
  blocked_id: string;
  created_at: string;
  blocked: { display_name: string; avatar_url: string | null } | null;
}

/**
 * Block someone.
 *
 * The feed hides drops in both directions from that moment on, and the
 * response trigger refuses joins between the two of you. Blocking is silent:
 * the other person is never told, and cannot read the row — the blocks SELECT
 * policy only matches rows where you are the blocker.
 */
export async function blockUser(blockerId: string, blockedId: string): Promise<void> {
  const { error } = await supabase
    .from('blocks')
    .insert({ blocker_id: blockerId, blocked_id: blockedId });

  // Already blocked is the state the caller wanted, not a failure.
  if (error && error.code !== '23505') {
    throw toApiError(error, 'Could not block that person.');
  }
}

export async function unblockUser(blockerId: string, blockedId: string): Promise<void> {
  const { error } = await supabase
    .from('blocks')
    .delete()
    .eq('blocker_id', blockerId)
    .eq('blocked_id', blockedId);

  if (error) {
    throw toApiError(error, 'Could not unblock that person.');
  }
}

export async function listBlockedUsers(): Promise<BlockedUser[]> {
  // RLS narrows this to your own blocks; the FK hint disambiguates which of
  // the two profile references to follow.
  const { data, error } = await supabase
    .from('blocks')
    .select(
      'blocked_id, created_at, blocked:profiles!blocks_blocked_id_fkey(display_name, avatar_url)',
    )
    .order('created_at', { ascending: false })
    .returns<BlockRow[]>();

  if (error) {
    throw toApiError(error, 'Could not load your blocked list.');
  }

  return (data ?? []).map((row) => ({
    user_id: row.blocked_id,
    display_name: row.blocked?.display_name ?? 'Someone',
    avatar_url: row.blocked?.avatar_url ?? null,
    blocked_at: row.created_at,
  }));
}

/**
 * File a report. Write-only from the client: there is an INSERT policy and no
 * SELECT policy, so nobody — including the reporter — can read these back.
 * Moderators use the admin schema with the service role.
 */
export async function reportContent(
  reporterId: string,
  targetType: ReportTarget,
  targetId: string,
  reason: string,
): Promise<void> {
  const { error } = await supabase.from('reports').insert({
    reporter_id: reporterId,
    target_type: targetType,
    target_id: targetId,
    reason,
  });

  if (error) {
    throw toApiError(error, 'Could not send that report.');
  }
}
