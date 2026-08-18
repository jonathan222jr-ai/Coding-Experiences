import { supabase } from '../lib/supabase';
import type { DropCategory, DropStatus, ThreadRow } from '../types/database';
import { toApiError } from './errors';

export type { ThreadRow };

/** The drop a thread was born from. */
export interface ThreadDrop {
  id: string;
  user_id: string;
  body: string;
  category: DropCategory;
  status: DropStatus;
  expires_at: string;
  created_at: string;
  gif_url: string | null;
  gif_width: number | null;
  gif_height: number | null;
  gif_alt: string | null;
}

export interface ThreadMember {
  user_id: string;
  display_name: string;
  avatar_url: string | null;
  joined_at: string;
}

export interface ThreadDetail {
  id: string;
  created_at: string;
  drop: ThreadDrop;
  members: ThreadMember[];
}

/**
 * Threads you belong to, most recently active first, each with a preview of
 * its last message. One RPC rather than N+1 queries over thread_users.
 */
export async function fetchThreads(): Promise<ThreadRow[]> {
  const { data, error } = await supabase.rpc('get_threads');

  if (error) {
    throw toApiError(error, 'Could not load your threads.');
  }

  return data ?? [];
}

interface ThreadUserRow {
  user_id: string;
  joined_at: string;
  profile: { display_name: string; avatar_url: string | null } | null;
}

/**
 * The thread's drop and its members.
 *
 * The member list doubles as the name lookup for chat: realtime delivers raw
 * message rows with a user_id and no display name, and a thread is capped at
 * six people, so resolving names from this map beats joining profiles on
 * every message.
 */
export async function fetchThreadDetail(threadId: string): Promise<ThreadDetail> {
  const [threadResult, memberResult] = await Promise.all([
    supabase
      .from('threads')
      .select(
        'id, created_at, drop:drops(id, user_id, body, category, status, expires_at, created_at, gif_url, gif_width, gif_height, gif_alt)',
      )
      .eq('id', threadId)
      .single()
      .returns<{ id: string; created_at: string; drop: ThreadDrop }>(),
    supabase
      .from('thread_users')
      .select('user_id, joined_at, profile:profiles(display_name, avatar_url)')
      .eq('thread_id', threadId)
      .order('joined_at')
      .returns<ThreadUserRow[]>(),
  ]);

  if (threadResult.error) {
    throw toApiError(threadResult.error, 'Could not open that thread.');
  }

  if (memberResult.error) {
    throw toApiError(memberResult.error, 'Could not load who is in this thread.');
  }

  return {
    id: threadResult.data.id,
    created_at: threadResult.data.created_at,
    drop: threadResult.data.drop,
    members: (memberResult.data ?? []).map((row) => ({
      user_id: row.user_id,
      display_name: row.profile?.display_name ?? 'Someone',
      avatar_url: row.profile?.avatar_url ?? null,
      joined_at: row.joined_at,
    })),
  };
}
