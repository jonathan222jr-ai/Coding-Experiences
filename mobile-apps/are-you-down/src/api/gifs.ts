import { FunctionsHttpError } from '@supabase/supabase-js';

import { supabase } from '../lib/supabase';
import { ApiError } from './errors';

export interface Gif {
  id: string;
  url: string;
  previewUrl: string;
  width: number;
  height: number;
  alt: string;
}

/**
 * A GIF search that failed.
 *
 * `unconfigured` separates "this deployment has no Tenor key" from "Tenor is
 * having a bad day". They need different words on screen and, more to the
 * point, different actions: one is a retry, the other is a deploy.
 */
export class GifSearchError extends ApiError {
  readonly unconfigured: boolean;

  constructor(message: string, unconfigured = false) {
    super(message);
    this.name = 'GifSearchError';
    this.unconfigured = unconfigured;
    Object.setPrototypeOf(this, GifSearchError.prototype);
  }
}

/**
 * The proxy answers a failure with `{ error }` and a status. supabase-js wraps
 * that in a FunctionsHttpError whose message is just "Edge Function returned a
 * non-2xx status code" — the function's own sentence is in the untouched
 * Response hanging off `context`, so read it rather than discarding it.
 */
async function describeFailure(error: unknown): Promise<GifSearchError> {
  if (error instanceof FunctionsHttpError) {
    const status = error.context.status;

    try {
      const body = (await error.context.json()) as { error?: string };

      if (typeof body.error === 'string') {
        return new GifSearchError(body.error, status === 503);
      }
    } catch {
      // A non-JSON body (a gateway's HTML error page, say) tells us nothing
      // worth showing; fall through to the generic message.
    }

    // 404 means the function isn't deployed at all, which is the same problem
    // to the person holding the phone as a missing key.
    if (status === 404 || status === 503) {
      return new GifSearchError('GIF search is not set up yet.', true);
    }
  }

  return new GifSearchError("Couldn't load GIFs. Try again in a moment.");
}

/**
 * Search GIFs through our own proxy rather than Tenor directly.
 *
 * The API key stays server-side, and — more importantly — so does
 * `contentfilter=high`. If the client built the query, the strictest safety
 * setting would be one edited request away from being off for everyone.
 *
 * An empty query is not an empty result: the proxy answers it with Tenor's
 * featured set, so opening the picker shows something.
 */
export async function searchGifs(query: string): Promise<Gif[]> {
  const { data, error } = await supabase.functions.invoke<{ gifs: Gif[] }>(
    `gif-search?q=${encodeURIComponent(query.trim())}`,
    { method: 'GET' },
  );

  if (error) {
    throw await describeFailure(error);
  }

  return data?.gifs ?? [];
}
