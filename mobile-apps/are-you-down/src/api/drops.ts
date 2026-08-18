import { supabase } from '../lib/supabase';
import type { DropCategory, FeedRow, Tables } from '../types/database';
import { ApiError, toApiError } from './errors';
import type { Gif } from './gifs';

export type Drop = Tables<'drops'>;
export type { FeedRow };

export const DROP_BODY_MAX = 140;

/** Keyset cursor: the (created_at, id) of the last row already rendered. */
export interface FeedCursor {
  createdAt: string;
  id: string;
}

export interface FeedPage {
  drops: FeedRow[];
  nextCursor: FeedCursor | null;
}

export const FEED_PAGE_SIZE = 20;

/**
 * One page of the campus feed, optionally narrowed to one category group.
 *
 * All the filtering — campus scoping, own drops, already-answered drops, blocks
 * in either direction, expiry, and the group — happens inside get_feed(). Doing
 * it here would be both slower and a lie, since anything the client filters it
 * must first have been allowed to read; and a client-side group filter would
 * shrink each page rather than the result set, so "no boba drops" and "end of
 * the feed" would look identical.
 */
export async function fetchFeed(
  cursor: FeedCursor | null = null,
  limit: number = FEED_PAGE_SIZE,
  group: string | null = null,
): Promise<FeedPage> {
  const { data, error } = await supabase.rpc('get_feed', {
    p_limit: limit,
    p_before_created_at: cursor?.createdAt ?? null,
    p_before_id: cursor?.id ?? null,
    p_group: group,
  });

  if (error) {
    throw toApiError(error, 'Could not load the feed.');
  }

  const drops = data ?? [];
  const last = drops[drops.length - 1];

  return {
    drops,
    // A short page means we've reached the end; only hand back a cursor when a
    // full page came through.
    nextCursor:
      drops.length === limit && last ? { createdAt: last.created_at, id: last.id } : null,
  };
}

export interface CreateDropInput {
  userId: string;
  schoolId: string;
  body: string;
  category: DropCategory;
  expiresAt: Date;
  /** Optional, and only ever one that came back from the search proxy. */
  gif?: Gif | null;
}

export async function createDrop(input: CreateDropInput): Promise<Drop> {
  const body = input.body.trim();

  // A GIF is an addition to the sentence, never a replacement for it — the
  // column is NOT NULL for the same reason. Checked here only to say it
  // nicely; the constraint is what enforces it.
  if (body.length === 0) {
    throw new ApiError('Say what you want to do.');
  }

  if (body.length > DROP_BODY_MAX) {
    throw new ApiError(`Keep it under ${DROP_BODY_MAX} characters.`);
  }

  const gif = input.gif ?? null;

  const { data, error } = await supabase
    .from('drops')
    .insert({
      user_id: input.userId,
      school_id: input.schoolId,
      body,
      category: input.category,
      expires_at: input.expiresAt.toISOString(),
      gif_id: gif?.id ?? null,
      gif_url: gif?.url ?? null,
      gif_preview_url: gif?.previewUrl ?? null,
      gif_width: gif?.width ?? null,
      gif_height: gif?.height ?? null,
      gif_alt: gif?.alt ?? null,
    })
    .select()
    .single();

  if (error) {
    throw toApiError(error, 'Could not post your drop.');
  }

  return data;
}

/**
 * The caller's own live drops.
 *
 * The feed deliberately excludes these, so without this the app would swallow
 * your post the moment you made it.
 */
export async function fetchMyActiveDrops(userId: string): Promise<Drop[]> {
  const { data, error } = await supabase
    .from('drops')
    .select('*')
    .eq('user_id', userId)
    .eq('status', 'open')
    .gt('expires_at', new Date().toISOString())
    .order('created_at', { ascending: false });

  if (error) {
    throw toApiError(error, 'Could not load your drops.');
  }

  return data ?? [];
}

export async function closeDrop(dropId: string): Promise<Drop> {
  const { data, error } = await supabase
    .from('drops')
    .update({ status: 'closed' })
    .eq('id', dropId)
    .select()
    .single();

  if (error) {
    throw toApiError(error, 'Could not close that drop.');
  }

  return data;
}
