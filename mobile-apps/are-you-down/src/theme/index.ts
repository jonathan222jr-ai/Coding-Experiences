export const colors = {
  bg: '#0E0F13',
  surface: '#191B22',
  surfaceRaised: '#22252E',
  border: '#2E323D',
  text: '#F5F6F8',
  textMuted: '#9AA0AE',
  accent: '#FF5B5B',
  accentText: '#FFFFFF',
  down: '#3DDC84',
  pass: '#3A3F4B',
  danger: '#FF6B6B',
} as const;

export const spacing = {
  xs: 4,
  sm: 8,
  md: 12,
  lg: 16,
  xl: 24,
  xxl: 32,
} as const;

export const radius = {
  sm: 8,
  md: 14,
  lg: 20,
  pill: 999,
} as const;

// Category labels, emoji, and group colours intentionally do NOT live here any
// more. They come from the `categories` and `category_groups` tables via
// useCategories(), so a new category is an INSERT rather than a migration plus
// an app release.

/** Used when a category's group is unknown, or hasn't loaded yet. */
export const NEUTRAL_TINT = colors.textMuted;

const HEX = /^#[0-9A-Fa-f]{6}$/;

/**
 * A group colour at a given opacity, as an 8-digit hex string.
 *
 * Colours arrive from the database as six-digit hex — a CHECK constraint
 * guarantees it — so adding an alpha channel is concatenation rather than a
 * parse. The shape is re-checked here anyway: an app running against a database
 * that predates the colour column would otherwise render every chip
 * transparent, which looks like a layout bug rather than a missing migration.
 */
export function tint(color: string | undefined | null, alpha: number): string {
  const base = color && HEX.test(color) ? color : NEUTRAL_TINT;
  const channel = Math.round(Math.min(Math.max(alpha, 0), 1) * 255)
    .toString(16)
    .padStart(2, '0');

  return `${base}${channel}`;
}

/** Chip fill, chip border, and text, all derived from one group colour. */
export const tintAlpha = { fill: 0.16, border: 0.42 } as const;
