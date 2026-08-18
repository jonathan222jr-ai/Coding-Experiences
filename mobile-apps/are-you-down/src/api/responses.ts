import { supabase } from '../lib/supabase';
import type { ResponseType, Tables } from '../types/database';
import { ApiError, toApiError } from './errors';

export type Response = Tables<'responses'>;

/**
 * Answer a drop. One row, and the database does the rest.
 *
 * A 'pass' is recorded and nothing else happens — it is never shown to the
 * author or anyone else, it only stops the drop coming back in your feed.
 *
 * A 'down' fires handle_response(), which creates the thread on the first one,
 * seats the author, adds you, and refuses if the drop is closed, expired, full
 * at six, from another campus, or involves a block. Those rules are not
 * re-checked here on purpose: the trigger is the only thing that can enforce
 * them without a race, and it returns a message worth showing.
 */
export async function respondToDrop(
  dropId: string,
  userId: string,
  type: ResponseType,
): Promise<void> {
  const { error } = await supabase.from('responses').insert({
    drop_id: dropId,
    user_id: userId,
    type,
  });

  if (error) {
    throw toApiError(
      error,
      type === 'down' ? 'Could not join that one.' : 'Could not skip that one.',
    );
  }
}

/**
 * Postgres errors that mean the drop is genuinely unanswerable — it closed,
 * expired, filled up, or you already answered it. The card should disappear
 * rather than spring back for another doomed attempt.
 *
 * Anything else (a dropped connection, a timeout) leaves the drop answerable,
 * so the card comes back.
 */
const TERMINAL_CODES = new Set(['P0001', 'P0002', '23505', '42501']);

export function isTerminalResponseError(error: unknown): boolean {
  return error instanceof ApiError && error.code !== undefined && TERMINAL_CODES.has(error.code);
}
