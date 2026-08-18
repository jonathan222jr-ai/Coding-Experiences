import type { RealtimeChannel } from '@supabase/supabase-js';

import { supabase } from '../lib/supabase';
import type { Tables } from '../types/database';
import { ApiError, toApiError } from './errors';

export type Message = Tables<'messages'>;

export const MESSAGE_MAX = 1000;
export const MESSAGE_PAGE_SIZE = 50;

/**
 * A page of messages, newest first.
 *
 * The chat list is inverted, so "newest first" is also render order — no
 * reversing on either side.
 */
export async function fetchMessages(
  threadId: string,
  before?: string | null,
  limit: number = MESSAGE_PAGE_SIZE,
): Promise<Message[]> {
  let query = supabase
    .from('messages')
    .select('*')
    .eq('thread_id', threadId)
    .order('created_at', { ascending: false })
    .limit(limit);

  if (before) {
    query = query.lt('created_at', before);
  }

  const { data, error } = await query;

  if (error) {
    throw toApiError(error, 'Could not load this conversation.');
  }

  return data ?? [];
}

export interface OutgoingGif {
  id: string;
  url: string;
  previewUrl: string;
  width: number;
  height: number;
  alt: string;
}

/**
 * Send text, a GIF, or both.
 *
 * The database enforces that a message carries at least one of the two, and
 * that any GIF URL points at Tenor's CDN — so the checks here are only for a
 * nicer error message, not for correctness.
 */
export async function sendMessage(
  threadId: string,
  userId: string,
  rawBody: string,
  gif?: OutgoingGif | null,
): Promise<Message> {
  const body = rawBody.trim();

  if (body.length === 0 && !gif) {
    throw new ApiError('Type something first.');
  }

  if (body.length > MESSAGE_MAX) {
    throw new ApiError('That message is too long.');
  }

  const { data, error } = await supabase
    .from('messages')
    .insert({
      thread_id: threadId,
      user_id: userId,
      body: body.length > 0 ? body : null,
      ...(gif
        ? {
            gif_id: gif.id,
            gif_url: gif.url,
            gif_preview_url: gif.previewUrl,
            gif_width: gif.width,
            gif_height: gif.height,
            gif_alt: gif.alt,
          }
        : {}),
    })
    .select()
    .single();

  if (error) {
    throw toApiError(error, 'Could not send that.');
  }

  return data;
}

export type ThreadChannelStatus = 'joining' | 'live' | 'error';

interface SubscribeOptions {
  onMessage: (message: Message) => void;
  onStatusChange: (status: ThreadChannelStatus) => void;
}

/**
 * Stream new messages in a thread.
 *
 * RLS applies to the replication stream too, so a non-member subscribing to
 * this channel receives nothing — the filter below is for efficiency, not
 * access control.
 *
 * Only INSERTs are streamed; messages are never edited or deleted, so there is
 * no need for a replica identity beyond the default.
 */
export function subscribeToThread(
  threadId: string,
  { onMessage, onStatusChange }: SubscribeOptions,
): () => void {
  const channel: RealtimeChannel = supabase
    .channel(`thread:${threadId}`)
    .on(
      'postgres_changes',
      {
        event: 'INSERT',
        schema: 'public',
        table: 'messages',
        filter: `thread_id=eq.${threadId}`,
      },
      (payload) => onMessage(payload.new as Message),
    )
    .subscribe((status) => {
      if (status === 'SUBSCRIBED') {
        onStatusChange('live');
      } else if (status === 'CHANNEL_ERROR' || status === 'TIMED_OUT') {
        onStatusChange('error');
      } else if (status === 'CLOSED') {
        onStatusChange('joining');
      }
    });

  return () => {
    void supabase.removeChannel(channel);
  };
}
