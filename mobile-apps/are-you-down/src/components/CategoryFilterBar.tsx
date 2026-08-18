import { Pressable, ScrollView, StyleSheet, Text } from 'react-native';

import { useCategories } from '../hooks/useCategories';
import { colors, radius, spacing, tint, tintAlpha } from '../theme';

interface CategoryFilterBarProps {
  /** Group slug, or null for everything. */
  value: string | null;
  onChange: (group: string | null) => void;
}

/**
 * The six category groups, as a filter over the feed.
 *
 * This is the only place the grouping is stated outright, which is the point:
 * before it, a category was a decoration on a card rather than something you
 * could use. Filtering happens inside get_feed() — filtering here would mean
 * paging through drops only to throw them away, and would make "no results"
 * indistinguishable from "end of feed".
 */
export function CategoryFilterBar({ value, onChange }: CategoryFilterBarProps) {
  const { menu } = useCategories();

  return (
    <ScrollView
      horizontal
      showsHorizontalScrollIndicator={false}
      // A ScrollView's own default style is `flexGrow: 1, flexShrink: 1`. Left
      // alone next to the feed's list — also a ScrollView, with far more
      // content — this one gets shrunk below its natural height and clips the
      // chip labels in half.
      style={styles.bar}
      contentContainerStyle={styles.row}
      // Chips are small targets next to a vertically scrolling list; without
      // this a slightly-off horizontal swipe scrolls the feed instead.
      directionalLockEnabled
    >
      <FilterChip
        label="All"
        color={colors.text}
        selected={value === null}
        onPress={() => onChange(null)}
      />

      {(menu?.groups ?? []).map((group) => (
        <FilterChip
          key={group.slug}
          label={group.label}
          color={group.color}
          selected={value === group.slug}
          // Tapping the active group clears it, so the filter never becomes a
          // state you have to hunt for the exit from.
          onPress={() => onChange(value === group.slug ? null : group.slug)}
        />
      ))}
    </ScrollView>
  );
}

function FilterChip({
  label,
  color,
  selected,
  onPress,
}: {
  label: string;
  color: string;
  selected: boolean;
  onPress: () => void;
}) {
  return (
    <Pressable
      accessibilityRole="button"
      accessibilityState={{ selected }}
      onPress={onPress}
      style={({ pressed }) => [
        styles.chip,
        {
          backgroundColor: selected ? tint(color, 0.9) : tint(color, tintAlpha.fill),
          borderColor: tint(color, selected ? 0.9 : tintAlpha.border),
        },
        pressed ? styles.pressed : null,
      ]}
    >
      <Text style={[styles.label, { color: selected ? colors.bg : color }]}>{label}</Text>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  bar: { flexGrow: 0, flexShrink: 0 },
  row: {
    flexDirection: 'row',
    gap: spacing.sm,
    paddingHorizontal: spacing.lg,
    paddingBottom: spacing.md,
  },
  chip: {
    borderRadius: radius.pill,
    borderWidth: 1,
    paddingHorizontal: spacing.lg - 2,
    paddingVertical: spacing.sm,
  },
  pressed: { opacity: 0.7 },
  label: { fontSize: 14, fontWeight: '700' },
});
