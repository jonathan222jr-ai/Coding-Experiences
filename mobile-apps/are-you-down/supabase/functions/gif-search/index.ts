/**
 * GIF search proxy.
 *
 * The app never talks to Tenor directly, for two reasons:
 *
 *  1. The API key stays here. An `EXPO_PUBLIC_` key is inlined into the shipped
 *     bundle and can be lifted out of it in about a minute.
 *  2. `contentfilter=high` is enforced server-side. If the client built the
 *     query, the strictest safety setting would be one edited request away from
 *     being turned off — by anyone, for everyone.
 *
 * Supabase verifies the caller's JWT before this runs, so only signed-in
 * students reach it.
 *
 * Deploy:  npx supabase functions deploy gif-search
 * Secrets: npx supabase secrets set TENOR_API_KEY=...
 */

const TENOR = 'https://tenor.googleapis.com/v2';

// Tenor's strictest rating. Not a guarantee — no provider's filter is — but it
// is the floor, and the client cannot lower it.
const CONTENT_FILTER = 'high';

const LIMIT = 24;

interface TenorMedia {
  url: string;
  dims?: [number, number];
}

interface TenorResult {
  id: string;
  content_description?: string;
  media_formats?: Record<string, TenorMedia>;
}

export interface Gif {
  id: string;
  url: string;
  previewUrl: string;
  width: number;
  height: number;
  alt: string;
}

function json(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json' },
  });
}

function normalise(results: TenorResult[]): Gif[] {
  const gifs: Gif[] = [];

  for (const result of results) {
    // tinygif for the grid, gif for the bubble. Both are on the same CDN the
    // messages_gif_host constraint pins to.
    const full = result.media_formats?.gif ?? result.media_formats?.mediumgif;
    const preview = result.media_formats?.tinygif ?? full;

    if (!full?.url || !preview?.url) continue;

    gifs.push({
      id: result.id,
      url: full.url,
      previewUrl: preview.url,
      width: full.dims?.[0] ?? 0,
      height: full.dims?.[1] ?? 0,
      alt: result.content_description ?? 'GIF',
    });
  }

  return gifs;
}

Deno.serve(async (req: Request): Promise<Response> => {
  const key = Deno.env.get('TENOR_API_KEY');

  if (!key) {
    return json({ error: 'GIF search is not configured.' }, 503);
  }

  const url = new URL(req.url);
  const query = (url.searchParams.get('q') ?? '').trim().slice(0, 100);

  // An empty query means the picker just opened — show what's trending rather
  // than an empty grid.
  const endpoint = query.length > 0 ? 'search' : 'featured';

  const params = new URLSearchParams({
    key,
    client_key: 'are_you_down',
    contentfilter: CONTENT_FILTER,
    media_filter: 'gif,tinygif,mediumgif',
    limit: String(LIMIT),
  });

  if (query.length > 0) params.set('q', query);

  try {
    const response = await fetch(`${TENOR}/${endpoint}?${params}`);

    if (!response.ok) {
      return json({ error: 'GIF search is unavailable right now.' }, 502);
    }

    const body = await response.json();

    return json(
      { gifs: normalise(body.results ?? []) },
      200,
    );
  } catch {
    return json({ error: 'GIF search is unavailable right now.' }, 502);
  }
});
