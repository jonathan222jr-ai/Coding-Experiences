import { useNavigation } from '@react-navigation/native';
import { useMemo, useState } from 'react';
import {
  KeyboardAvoidingView,
  Platform,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  View,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { createDrop, DROP_BODY_MAX } from '../api/drops';
import type { Gif } from '../api/gifs';
import { Button } from '../components/Button';
import { GifImage } from '../components/GifImage';
import { GifPicker } from '../components/GifPicker';
import { Sheet } from '../components/Sheet';
import { useCurrentUser } from '../hooks/useAuth';
import { useCategories } from '../hooks/useCategories';
import { EXPIRY_CHOICES, resolveExpiry, type ExpiryOption } from '../lib/time';
import { NEUTRAL_TINT, colors, radius, spacing, tint, tintAlpha } from '../theme';

/** Smaller than the card it will appear in — this is a confirmation, not a preview. */
const GIF_PREVIEW_WIDTH = 200;

export function CreateDropScreen() {
  const navigation = useNavigation();
  const { userId, profile } = useCurrentUser();

  const [body, setBody] = useState('');
  const { menu, error: menuError } = useCategories();
  const [category, setCategory] = useState<string>('hangout');
  // Which group's categories are showing. With ~35 of them a flat chip wall is
  // unusable, so the groups act as tabs over one row of choices. Null means
  // "follow the selection", which is what makes the screen open on the group
  // the current category belongs to instead of an arbitrary one.
  const [browsingGroup, setBrowsingGroup] = useState<string | null>(null);
  const [expiry, setExpiry] = useState<ExpiryOption>('2h');
  const [gif, setGif] = useState<Gif | null>(null);
  const [pickingGif, setPickingGif] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const remaining = DROP_BODY_MAX - body.length;
  const canPost = body.trim().length > 0 && remaining >= 0 && !busy;

  const selected = menu?.bySlug[category] ?? null;
  const openGroup = browsingGroup ?? selected?.group_slug ?? menu?.groups[0]?.slug ?? null;
  const openGroupColor = openGroup
    ? (menu?.groupBySlug[openGroup]?.color ?? NEUTRAL_TINT)
    : NEUTRAL_TINT;

  // The colour the card will carry in the feed. Shown next to the section
  // heading so the choice is visible even while a different group is open.
  const selectedColor = useMemo(() => {
    const group = selected ? menu?.groupBySlug[selected.group_slug] : undefined;
    return group?.color ?? NEUTRAL_TINT;
  }, [menu, selected]);

  // Recomputed per render so the "until 9:41pm" hint doesn't go stale while
  // the user sits on this screen.
  const expiryHint = useMemo(() => {
    const choice = EXPIRY_CHOICES.find((option) => option.value === expiry);
    return choice ? choice.describe(new Date()) : '';
  }, [expiry]);

  const post = async () => {
    setBusy(true);
    setError(null);

    try {
      await createDrop({
        userId,
        schoolId: profile.school_id,
        body,
        category,
        expiresAt: resolveExpiry(expiry),
        gif,
      });
      navigation.goBack();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
      setBusy(false);
    }
  };

  return (
    <SafeAreaView style={styles.safe}>
      <KeyboardAvoidingView
        style={styles.flex}
        behavior={Platform.OS === 'ios' ? 'padding' : undefined}
      >
        <View style={styles.header}>
          <Pressable onPress={() => navigation.goBack()} accessibilityRole="button">
            <Text style={styles.cancel}>Cancel</Text>
          </Pressable>
          <Text style={styles.headerTitle}>New drop</Text>
          <View style={styles.headerSpacer} />
        </View>

        <ScrollView
          contentContainerStyle={styles.content}
          keyboardShouldPersistTaps="handled"
        >
          <View style={styles.inputWrap}>
            <TextInput
              value={body}
              onChangeText={setBody}
              placeholder="Are you down to..."
              placeholderTextColor={colors.textMuted}
              style={styles.input}
              multiline
              autoFocus
              maxLength={DROP_BODY_MAX}
              editable={!busy}
            />
            <Text style={[styles.counter, remaining <= 20 ? styles.counterLow : null]}>
              {remaining}
            </Text>
          </View>

          <Section
            title="GIF"
            hint={<Text style={styles.sectionHint}>Optional</Text>}
          >
            {gif ? (
              <View style={styles.gifPicked}>
                <GifImage
                  url={gif.url}
                  width={gif.width}
                  height={gif.height}
                  alt={gif.alt}
                  maxWidth={GIF_PREVIEW_WIDTH}
                />

                <View style={styles.gifActions}>
                  <Button
                    label="Swap"
                    variant="secondary"
                    onPress={() => setPickingGif(true)}
                    disabled={busy}
                    style={styles.gifAction}
                  />
                  <Button
                    label="Remove"
                    variant="ghost"
                    onPress={() => setGif(null)}
                    disabled={busy}
                    style={styles.gifAction}
                  />
                </View>
              </View>
            ) : (
              <Button
                label="Add a GIF"
                variant="secondary"
                onPress={() => setPickingGif(true)}
                disabled={busy}
              />
            )}
          </Section>

          <Section
            title="Category"
            hint={
              selected ? (
                <View
                  style={[
                    styles.selectedChip,
                    {
                      backgroundColor: tint(selectedColor, tintAlpha.fill),
                      borderColor: tint(selectedColor, tintAlpha.border),
                    },
                  ]}
                >
                  <Text style={[styles.selectedChipText, { color: selectedColor }]}>
                    {selected.emoji} {selected.label}
                  </Text>
                </View>
              ) : null
            }
          >
            <Text style={styles.sectionNote}>
              Pick the group, then the thing. It colours your card and it's how
              people filter the feed.
            </Text>

            {/* Groups are tabs, not choices. They used to be the same pill as
                the categories below, which made "Out" selected look exactly
                like "Hangout" selected — two different meanings, one control. */}
            <ScrollView
              horizontal
              showsHorizontalScrollIndicator={false}
              // See CategoryFilterBar: a ScrollView defaults to flexGrow/
              // flexShrink 1 and will be squeezed by a taller sibling.
              style={styles.tabScroll}
              contentContainerStyle={styles.tabRow}
              directionalLockEnabled
            >
              {(menu?.groups ?? []).map((group) => {
                const open = openGroup === group.slug;

                return (
                  <Pressable
                    key={group.slug}
                    accessibilityRole="tab"
                    accessibilityState={{ selected: open, disabled: busy }}
                    disabled={busy}
                    onPress={() => setBrowsingGroup(group.slug)}
                    style={({ pressed }) => [styles.tab, pressed ? styles.pressed : null]}
                  >
                    <Text
                      style={[
                        styles.tabText,
                        open ? { color: group.color } : null,
                      ]}
                    >
                      {group.label}
                    </Text>
                    <View
                      style={[
                        styles.tabUnderline,
                        { backgroundColor: open ? group.color : 'transparent' },
                      ]}
                    />
                  </Pressable>
                );
              })}
            </ScrollView>

            {menu === null ? (
              <Text style={styles.pickerNote}>
                {menuError ?? 'Loading categories…'}
              </Text>
            ) : (
              <View style={styles.chipRow}>
                {(openGroup ? (menu.byGroup[openGroup] ?? []) : []).map((option) => {
                  const on = category === option.slug;

                  return (
                    <Pressable
                      key={option.slug}
                      accessibilityRole="button"
                      accessibilityState={{ selected: on, disabled: busy }}
                      disabled={busy}
                      onPress={() => setCategory(option.slug)}
                      style={({ pressed }) => [
                        styles.selectChip,
                        {
                          backgroundColor: on
                            ? tint(openGroupColor, 0.9)
                            : tint(openGroupColor, tintAlpha.fill),
                          borderColor: tint(openGroupColor, on ? 0.9 : tintAlpha.border),
                        },
                        pressed ? styles.pressed : null,
                      ]}
                    >
                      <Text
                        style={[
                          styles.selectChipText,
                          { color: on ? colors.bg : openGroupColor },
                        ]}
                      >
                        {option.emoji} {option.label}
                      </Text>
                    </Pressable>
                  );
                })}
              </View>
            )}
          </Section>

          <Section title="Expires" hint={<Text style={styles.sectionHint}>{expiryHint}</Text>}>
            <View style={styles.chipRow}>
              {EXPIRY_CHOICES.map((option) => (
                <SelectChip
                  key={option.value}
                  label={option.label}
                  selected={expiry === option.value}
                  onPress={() => setExpiry(option.value)}
                  disabled={busy}
                />
              ))}
            </View>
          </Section>

          {error ? <Text style={styles.error}>{error}</Text> : null}

          <Button
            label="Post it"
            onPress={() => void post()}
            disabled={!canPost}
            loading={busy}
          />

          <Text style={styles.footnote}>
            Everyone at {profile.school.name} can see this until it expires. Meet
            in a public place.
          </Text>
        </ScrollView>
      </KeyboardAvoidingView>

      {/* This screen is itself presented modally, but that's a native-stack
          modal rather than a second RN Modal, so the sheet still presents. */}
      <Sheet
        visible={pickingGif}
        title="Add a GIF"
        subtitle="Everyone on campus sees this one, not just the people who join."
        onClose={() => setPickingGif(false)}
      >
        <GifPicker
          onPick={(picked) => {
            setGif(picked);
            setPickingGif(false);
          }}
        />
      </Sheet>
    </SafeAreaView>
  );
}

function Section({
  title,
  hint,
  children,
}: {
  title: string;
  /** Rendered opposite the title — a plain string of text, or a chip. */
  hint?: React.ReactNode;
  children: React.ReactNode;
}) {
  return (
    <View style={styles.section}>
      <View style={styles.sectionHeader}>
        <Text style={styles.sectionTitle}>{title}</Text>
        {hint}
      </View>
      {children}
    </View>
  );
}

function SelectChip({
  label,
  selected,
  onPress,
  disabled,
}: {
  label: string;
  selected: boolean;
  onPress: () => void;
  disabled: boolean;
}) {
  return (
    <Pressable
      accessibilityRole="button"
      accessibilityState={{ selected, disabled }}
      disabled={disabled}
      onPress={onPress}
      style={({ pressed }) => [
        styles.selectChip,
        selected ? styles.selectChipOn : null,
        pressed ? styles.selectChipPressed : null,
      ]}
    >
      <Text style={[styles.selectChipText, selected ? styles.selectChipTextOn : null]}>
        {label}
      </Text>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: colors.bg },
  flex: { flex: 1 },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: spacing.lg,
    paddingVertical: spacing.md,
  },
  cancel: { color: colors.textMuted, fontSize: 16, width: 70 },
  headerTitle: { color: colors.text, fontSize: 16, fontWeight: '700' },
  headerSpacer: { width: 70 },
  content: { padding: spacing.lg, gap: spacing.xl },
  inputWrap: {
    backgroundColor: colors.surface,
    borderRadius: radius.md,
    borderWidth: 1,
    borderColor: colors.border,
    padding: spacing.lg,
  },
  input: {
    color: colors.text,
    fontSize: 20,
    lineHeight: 28,
    fontWeight: '600',
    minHeight: 96,
    textAlignVertical: 'top',
  },
  counter: { color: colors.textMuted, fontSize: 12, alignSelf: 'flex-end' },
  counterLow: { color: colors.accent },
  gifPicked: { gap: spacing.md, alignItems: 'flex-start' },
  gifActions: { flexDirection: 'row', gap: spacing.sm, alignSelf: 'stretch' },
  gifAction: { flex: 1 },
  section: { gap: spacing.md },
  sectionHeader: {
    flexDirection: 'row',
    alignItems: 'baseline',
    justifyContent: 'space-between',
  },
  sectionTitle: {
    color: colors.text,
    fontSize: 13,
    fontWeight: '800',
    letterSpacing: 0.6,
    textTransform: 'uppercase',
  },
  sectionHint: { color: colors.textMuted, fontSize: 13 },
  sectionNote: { color: colors.textMuted, fontSize: 13, lineHeight: 18, marginTop: -spacing.xs },
  selectedChip: {
    borderRadius: radius.pill,
    borderWidth: 1,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.xs + 1,
  },
  selectedChipText: { fontSize: 13, fontWeight: '700' },
  tabScroll: { flexGrow: 0, flexShrink: 0 },
  tabRow: { flexDirection: 'row', gap: spacing.lg, paddingRight: spacing.lg },
  tab: { gap: spacing.sm, alignItems: 'center' },
  tabText: { color: colors.textMuted, fontSize: 15, fontWeight: '700' },
  tabUnderline: { height: 3, alignSelf: 'stretch', borderRadius: radius.pill },
  pickerNote: { color: colors.textMuted, fontSize: 13 },
  pressed: { opacity: 0.75 },
  chipRow: { flexDirection: 'row', flexWrap: 'wrap', gap: spacing.sm },
  selectChip: {
    backgroundColor: colors.surface,
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: radius.pill,
    paddingHorizontal: spacing.lg,
    paddingVertical: spacing.md - 2,
  },
  selectChipOn: { backgroundColor: colors.accent, borderColor: colors.accent },
  selectChipPressed: { opacity: 0.75 },
  selectChipText: { color: colors.textMuted, fontSize: 14, fontWeight: '600' },
  selectChipTextOn: { color: colors.accentText },
  error: { color: colors.danger, fontSize: 14 },
  footnote: { color: colors.textMuted, fontSize: 12, lineHeight: 18 },
});
