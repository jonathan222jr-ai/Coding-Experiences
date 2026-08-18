import { supabase } from '../lib/supabase';
import { toApiError } from './errors';

/**
 * Remember this device's Expo push token.
 *
 * Keyed on (user_id, token) so signing in on a second device adds a row rather
 * than replacing one — the notify trigger fans out to every token the author
 * has.
 */
export async function savePushToken(userId: string, token: string): Promise<void> {
  const { error } = await supabase
    .from('push_tokens')
    .upsert(
      { user_id: userId, token, updated_at: new Date().toISOString() },
      { onConflict: 'user_id,token' },
    );

  if (error) {
    throw toApiError(error, 'Could not register this device for notifications.');
  }
}

export async function removePushToken(userId: string, token: string): Promise<void> {
  const { error } = await supabase
    .from('push_tokens')
    .delete()
    .eq('user_id', userId)
    .eq('token', token);

  if (error) {
    throw toApiError(error, 'Could not unregister this device.');
  }
}
