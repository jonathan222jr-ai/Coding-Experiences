import type { PostgrestError } from '@supabase/supabase-js';

/**
 * An error that already carries a message safe to show a user.
 *
 * The database is the authority on every rule in this app, so most failures
 * arrive as a Postgres error raised by a trigger or refused by a policy. This
 * turns them into something a screen can render without leaking SQL.
 */
export class ApiError extends Error {
  readonly code: string | undefined;

  constructor(message: string, code?: string) {
    super(message);
    this.name = 'ApiError';
    this.code = code;
    // Subclassing Error loses the prototype chain under some transpile
    // targets, which quietly breaks `instanceof ApiError`.
    Object.setPrototypeOf(this, ApiError.prototype);
  }
}

const FRIENDLY_BY_CODE: Record<string, string> = {
  // unique_violation — the (drop_id, user_id) constraint on responses
  '23505': "You've already answered this one.",
  // insufficient_privilege — raised by RLS and by our own triggers
  '42501': "You can't do that.",
  // raise_exception — our triggers pass a real message, handled below
  P0001: 'Something went wrong.',
  // no_data_found
  P0002: 'That no longer exists.',
};

export function toApiError(error: PostgrestError | Error | null, fallback: string): ApiError {
  if (!error) {
    return new ApiError(fallback);
  }

  if (error instanceof ApiError) {
    return error;
  }

  const code = 'code' in error ? (error.code as string | undefined) : undefined;

  // Messages we raise ourselves are already user-facing; prefer them over the
  // generic mapping.
  if (code === 'P0001' || code === '42501' || code === 'P0002') {
    return new ApiError(error.message || FRIENDLY_BY_CODE[code], code);
  }

  if (code && FRIENDLY_BY_CODE[code]) {
    return new ApiError(FRIENDLY_BY_CODE[code], code);
  }

  return new ApiError(fallback, code);
}
