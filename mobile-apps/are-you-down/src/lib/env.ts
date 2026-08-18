/**
 * Environment configuration.
 *
 * Expo inlines any `EXPO_PUBLIC_*` variable from .env at bundle time. Anything
 * in here ships inside the app binary, so only the anon key belongs here — the
 * service role key must never appear in this project.
 */

function required(name: string, value: string | undefined): string {
  if (!value) {
    throw new Error(
      `Missing ${name}. Copy .env.example to .env and fill in your Supabase ` +
        `project values, then restart the bundler with \`npx expo start -c\`.`,
    );
  }
  return value;
}

export const env = {
  supabaseUrl: required(
    'EXPO_PUBLIC_SUPABASE_URL',
    process.env.EXPO_PUBLIC_SUPABASE_URL,
  ),
  supabaseAnonKey: required(
    'EXPO_PUBLIC_SUPABASE_ANON_KEY',
    process.env.EXPO_PUBLIC_SUPABASE_ANON_KEY,
  ),
} as const;
