import { decode } from 'base64-arraybuffer';

import { supabase } from '../lib/supabase';
import { ApiError, toApiError } from './errors';

const BUCKET = 'avatars';

const EXTENSION_BY_MIME: Record<string, string> = {
  'image/jpeg': 'jpg',
  'image/png': 'png',
  'image/webp': 'webp',
};

export interface AvatarUpload {
  base64: string;
  mimeType: string;
}

/**
 * Upload an avatar and return its public URL.
 *
 * The path is `<user id>/<timestamp>.<ext>`, which is what the storage policies
 * key on — you can only write inside a folder named for your own id. The
 * timestamp busts any CDN cache that would otherwise keep serving the old
 * picture at the same URL.
 *
 * React Native has no reliable File/Blob for a local `file://` URI, so the
 * picker hands us base64 and we upload the decoded bytes directly.
 */
export async function uploadAvatar(
  userId: string,
  { base64, mimeType }: AvatarUpload,
): Promise<string> {
  const extension = EXTENSION_BY_MIME[mimeType];

  if (!extension) {
    throw new ApiError('Pick a JPEG, PNG, or WebP image.');
  }

  const path = `${userId}/${Date.now()}.${extension}`;

  const { error } = await supabase.storage
    .from(BUCKET)
    .upload(path, decode(base64), { contentType: mimeType, upsert: true });

  if (error) {
    throw toApiError(error, 'Could not upload that photo.');
  }

  // Best effort: drop the previous avatars so a user's folder doesn't grow
  // without bound. A leftover file is untidy, not broken, so failures here are
  // swallowed rather than surfaced.
  void pruneOldAvatars(userId, path);

  return supabase.storage.from(BUCKET).getPublicUrl(path).data.publicUrl;
}

async function pruneOldAvatars(userId: string, keepPath: string): Promise<void> {
  try {
    const { data } = await supabase.storage.from(BUCKET).list(userId);
    if (!data) return;

    const stale = data
      .map((file) => `${userId}/${file.name}`)
      .filter((candidate) => candidate !== keepPath);

    if (stale.length > 0) {
      await supabase.storage.from(BUCKET).remove(stale);
    }
  } catch {
    // Not worth telling the user about.
  }
}
