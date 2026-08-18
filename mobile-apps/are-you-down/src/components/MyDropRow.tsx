import { StyleSheet, Text, View } from 'react-native';

import type { Drop } from '../api/drops';
import { useCategories } from '../hooks/useCategories';
import { useNow } from '../hooks/useNow';
import { formatRemaining, isUrgent } from '../lib/time';
import { colors, radius, spacing } from '../theme';
import { CategoryBadge } from './CategoryChip';

/**
 * Your own live drop, pinned above the feed.
 *
 * get_feed() excludes your own posts by design, so without this the app would
 * appear to swallow whatever you just wrote.
 */
export function MyDropRow({ drop }: { drop: Drop }) {
  const now = useNow();
  const { describe } = useCategories();
  const remaining = formatRemaining(drop.expires_at, now);
  const urgent = isUrgent(drop.expires_at, now);

  return (
    <View style={styles.row}>
      <CategoryBadge category={drop.category} />

      <View style={styles.textColumn}>
        <Text style={styles.body} numberOfLines={2}>
          {drop.body}
        </Text>
        <Text style={styles.meta}>
          {describe(drop.category).label} · {remaining}
        </Text>
      </View>

      <View style={[styles.pulse, urgent ? styles.pulseUrgent : null]} />
    </View>
  );
}

const styles = StyleSheet.create({
  row: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.md,
    backgroundColor: colors.surfaceRaised,
    borderRadius: radius.md,
    borderWidth: 1,
    borderColor: colors.border,
    paddingHorizontal: spacing.lg,
    paddingVertical: spacing.md,
  },
  textColumn: { flex: 1, gap: 2 },
  body: { color: colors.text, fontSize: 15, fontWeight: '600' },
  meta: { color: colors.textMuted, fontSize: 12 },
  pulse: {
    width: 8,
    height: 8,
    borderRadius: radius.pill,
    backgroundColor: colors.down,
  },
  pulseUrgent: { backgroundColor: colors.accent },
});
