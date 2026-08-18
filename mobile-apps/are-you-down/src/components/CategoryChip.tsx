import { StyleSheet, Text, View } from 'react-native';

import { useCategories } from '../hooks/useCategories';
import { colors, radius, spacing, tint, tintAlpha } from '../theme';

/**
 * A category, tinted by its group.
 *
 * Thirty-five categories rendered in one grey used to mean the chip carried an
 * emoji and nothing else — you had to read every card to see what kind of thing
 * it was. Colour comes from `category_groups.color`, so the six groups are
 * distinguishable at a glance and a seventh group needs no app release.
 */
export function CategoryChip({ category }: { category: string }) {
  const { describe } = useCategories();
  const { label, emoji, color } = describe(category);

  return (
    <View
      style={[
        styles.chip,
        { backgroundColor: tint(color, tintAlpha.fill), borderColor: tint(color, tintAlpha.border) },
      ]}
    >
      <Text style={[styles.text, { color }]}>
        {emoji} {label}
      </Text>
    </View>
  );
}

/**
 * The same signal in list rows, where a full pill would crowd the title: the
 * emoji in a tinted square.
 */
export function CategoryBadge({ category }: { category: string }) {
  const { describe } = useCategories();
  const { emoji, color, label } = describe(category);

  return (
    <View
      style={[
        styles.badge,
        { backgroundColor: tint(color, tintAlpha.fill), borderColor: tint(color, tintAlpha.border) },
      ]}
      accessibilityLabel={label}
    >
      <Text style={styles.badgeEmoji}>{emoji}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  chip: {
    alignSelf: 'flex-start',
    borderRadius: radius.pill,
    borderWidth: 1,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.xs + 2,
  },
  text: { fontSize: 12, fontWeight: '700' },
  badge: {
    width: 38,
    height: 38,
    borderRadius: radius.md,
    borderWidth: 1,
    alignItems: 'center',
    justifyContent: 'center',
  },
  badgeEmoji: { fontSize: 18, color: colors.text },
});
