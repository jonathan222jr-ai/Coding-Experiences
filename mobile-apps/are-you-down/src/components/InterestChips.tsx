import { Pressable, StyleSheet, Text, View } from 'react-native';

import { useCategories } from '../hooks/useCategories';
import { colors, radius, spacing, tint, tintAlpha } from '../theme';

/** Read-only row of interest tags, used on the person screen. */
export function InterestChips({ slugs }: { slugs: string[] }) {
  const { describe } = useCategories();

  if (slugs.length === 0) return null;

  return (
    <View style={styles.row}>
      {slugs.map((slug) => {
        const { label, emoji, color } = describe(slug);
        return (
          <View
            key={slug}
            style={[
              styles.chip,
              {
                backgroundColor: tint(color, tintAlpha.fill),
                borderColor: tint(color, tintAlpha.border),
              },
            ]}
          >
            <Text style={[styles.text, { color }]}>
              {emoji} {label}
            </Text>
          </View>
        );
      })}
    </View>
  );
}

interface InterestPickerProps {
  selected: string[];
  onToggle: (slug: string) => void;
  disabled?: boolean;
  max: number;
}

/** Editable version: the same chips, grouped, with a cap. */
export function InterestPicker({
  selected,
  onToggle,
  disabled = false,
  max,
}: InterestPickerProps) {
  const { menu } = useCategories();
  const full = selected.length >= max;

  return (
    <View style={styles.groups}>
      {(menu?.groups ?? []).map((group) => (
        <View key={group.slug} style={styles.group}>
          <View style={styles.groupHeader}>
            <View style={[styles.groupDot, { backgroundColor: group.color }]} />
            <Text style={[styles.groupLabel, { color: group.color }]}>{group.label}</Text>
          </View>

          <View style={styles.row}>
            {(menu?.byGroup[group.slug] ?? []).map((category) => {
              const on = selected.includes(category.slug);
              // At the cap, only the already-chosen chips stay tappable, so
              // the limit reads as "swap one out" rather than a dead error.
              const blocked = disabled || (full && !on);

              return (
                <Pressable
                  key={category.slug}
                  accessibilityRole="button"
                  accessibilityState={{ selected: on, disabled: blocked }}
                  disabled={blocked}
                  onPress={() => onToggle(category.slug)}
                  style={({ pressed }) => [
                    styles.chip,
                    {
                      backgroundColor: on
                        ? tint(group.color, 0.9)
                        : tint(group.color, tintAlpha.fill),
                      borderColor: tint(group.color, on ? 0.9 : tintAlpha.border),
                    },
                    blocked ? styles.chipBlocked : null,
                    pressed ? styles.chipPressed : null,
                  ]}
                >
                  <Text style={[styles.text, { color: on ? colors.bg : group.color }]}>
                    {category.emoji} {category.label}
                  </Text>
                </Pressable>
              );
            })}
          </View>
        </View>
      ))}
    </View>
  );
}

const styles = StyleSheet.create({
  groups: { gap: spacing.lg },
  group: { gap: spacing.sm },
  groupHeader: { flexDirection: 'row', alignItems: 'center', gap: spacing.sm },
  groupDot: { width: 8, height: 8, borderRadius: radius.pill },
  groupLabel: {
    fontSize: 12,
    fontWeight: '800',
    letterSpacing: 0.6,
    textTransform: 'uppercase',
  },
  row: { flexDirection: 'row', flexWrap: 'wrap', gap: spacing.sm },
  chip: {
    backgroundColor: colors.surfaceRaised,
    borderRadius: radius.pill,
    borderWidth: 1,
    borderColor: colors.border,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm,
  },
  chipBlocked: { opacity: 0.35 },
  chipPressed: { opacity: 0.7 },
  text: { fontSize: 13, fontWeight: '600' },
});
