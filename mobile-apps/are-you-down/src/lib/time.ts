export type ExpiryOption = '30m' | '2h' | 'tonight';

export interface ExpiryChoice {
  value: ExpiryOption;
  label: string;
  describe: (from: Date) => string;
}

/**
 * "Tonight" means 11:59pm today. Past 11pm that would be a pointless window,
 * so it rolls to 2am — the small hours still read as "tonight" to anyone
 * awake enough to be posting.
 */
export function resolveExpiry(option: ExpiryOption, from: Date = new Date()): Date {
  switch (option) {
    case '30m':
      return new Date(from.getTime() + 30 * 60_000);
    case '2h':
      return new Date(from.getTime() + 2 * 60 * 60_000);
    case 'tonight': {
      const end = new Date(from);

      if (from.getHours() >= 23) {
        end.setDate(end.getDate() + 1);
        end.setHours(2, 0, 0, 0);
      } else {
        end.setHours(23, 59, 0, 0);
      }

      return end;
    }
  }
}

export const EXPIRY_CHOICES: ExpiryChoice[] = [
  {
    value: '30m',
    label: '30 min',
    describe: (from) => `until ${formatClock(resolveExpiry('30m', from))}`,
  },
  {
    value: '2h',
    label: '2 hours',
    describe: (from) => `until ${formatClock(resolveExpiry('2h', from))}`,
  },
  {
    value: 'tonight',
    label: 'Tonight',
    describe: (from) => `until ${formatClock(resolveExpiry('tonight', from))}`,
  },
];

export function formatClock(date: Date): string {
  const hours = date.getHours();
  const minutes = date.getMinutes().toString().padStart(2, '0');
  const suffix = hours >= 12 ? 'pm' : 'am';
  const display = hours % 12 === 0 ? 12 : hours % 12;
  return `${display}:${minutes}${suffix}`;
}

/**
 * Countdown label for a drop. Deliberately coarse above an hour — nobody needs
 * second-by-second precision on a three-hour window, and it keeps the string
 * from changing on every tick.
 */
export function formatRemaining(expiresAt: string, now: number): string {
  const remainingMs = new Date(expiresAt).getTime() - now;

  if (remainingMs <= 0) return 'expired';

  const totalMinutes = Math.floor(remainingMs / 60_000);

  if (totalMinutes < 1) {
    return `${Math.floor(remainingMs / 1000)}s left`;
  }

  if (totalMinutes < 60) {
    return `${totalMinutes}m left`;
  }

  const hours = Math.floor(totalMinutes / 60);
  const minutes = totalMinutes % 60;

  return minutes === 0 ? `${hours}h left` : `${hours}h ${minutes}m left`;
}

export function isUrgent(expiresAt: string, now: number): boolean {
  const remainingMs = new Date(expiresAt).getTime() - now;
  return remainingMs > 0 && remainingMs <= 10 * 60_000;
}

export function isExpired(expiresAt: string, now: number): boolean {
  return new Date(expiresAt).getTime() - now <= 0;
}

/** Short relative label for message and thread timestamps. */
export function formatAge(iso: string, now: number): string {
  const ageMs = now - new Date(iso).getTime();
  const minutes = Math.floor(ageMs / 60_000);

  if (minutes < 1) return 'now';
  if (minutes < 60) return `${minutes}m`;

  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h`;

  return `${Math.floor(hours / 24)}d`;
}
