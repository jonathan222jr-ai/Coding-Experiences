import { useFocusEffect } from '@react-navigation/native';
import { Image } from 'expo-image';
import * as ImagePicker from 'expo-image-picker';
import { useCallback, useState } from 'react';
import { Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { uploadAvatar } from '../api/avatars';
import {
  addInterest,
  BIO_MAX,
  CLASS_YEARS,
  fetchMyInterests,
  MAJOR_MAX,
  MAX_INTERESTS,
  PRONOUNS_MAX,
  removeInterest,
  updateProfile,
} from '../api/profiles';
import { listBlockedUsers, unblockUser, type BlockedUser } from '../api/safety';
import { Banner, type BannerMessage } from '../components/Banner';
import { Button } from '../components/Button';
import { InterestPicker } from '../components/InterestChips';
import { TextField } from '../components/TextField';
import { useAuth, useCurrentUser } from '../hooks/useAuth';
import { colors, radius, spacing } from '../theme';

export function ProfileScreen() {
  const { signOut, refreshProfile } = useAuth();
  const { userId, profile } = useCurrentUser();

  const [name, setName] = useState(profile.display_name);
  const [bio, setBio] = useState(profile.bio ?? '');
  const [pronouns, setPronouns] = useState(profile.pronouns ?? '');
  const [major, setMajor] = useState(profile.major ?? '');
  const [classYear, setClassYear] = useState<string | null>(profile.class_year);

  const [interests, setInterests] = useState<string[]>([]);
  const [saving, setSaving] = useState(false);
  const [signingOut, setSigningOut] = useState(false);
  const [uploadingAvatar, setUploadingAvatar] = useState(false);
  const [blocked, setBlocked] = useState<BlockedUser[] | null>(null);
  const [unblocking, setUnblocking] = useState<string | null>(null);
  const [banner, setBanner] = useState<BannerMessage | null>(null);

  const say = (tone: 'good' | 'bad', text: string) =>
    setBanner({ key: Date.now(), tone, text });

  const fail = (error: unknown) =>
    say('bad', error instanceof Error ? error.message : String(error));

  const load = useCallback(async () => {
    try {
      const [blockedUsers, myInterests] = await Promise.all([
        listBlockedUsers(),
        fetchMyInterests(userId),
      ]);
      setBlocked(blockedUsers);
      setInterests(myInterests);
    } catch (error) {
      fail(error);
    }
  }, [userId]);

  useFocusEffect(
    useCallback(() => {
      void load();
    }, [load]),
  );

  const dirty =
    name.trim() !== profile.display_name ||
    bio.trim() !== (profile.bio ?? '') ||
    pronouns.trim() !== (profile.pronouns ?? '') ||
    major.trim() !== (profile.major ?? '') ||
    classYear !== profile.class_year;

  const save = async () => {
    setSaving(true);
    try {
      await updateProfile(userId, {
        display_name: name,
        bio,
        pronouns,
        major,
        class_year: classYear,
      });
      await refreshProfile();
      say('good', 'Profile saved.');
    } catch (error) {
      fail(error);
    } finally {
      setSaving(false);
    }
  };

  // Interests save immediately rather than waiting for the Save button: the
  // six-item cap lives in a trigger, so the server has to be the thing that
  // says no, and finding that out on submit would lose the rest of the form.
  const toggleInterest = async (slug: string) => {
    const on = interests.includes(slug);
    const previous = interests;

    setInterests(on ? interests.filter((s) => s !== slug) : [...interests, slug]);

    try {
      if (on) {
        await removeInterest(userId, slug);
      } else {
        await addInterest(userId, slug);
      }
    } catch (error) {
      setInterests(previous);
      fail(error);
    }
  };

  const pickAvatar = async () => {
    try {
      const permission = await ImagePicker.requestMediaLibraryPermissionsAsync();

      if (!permission.granted) {
        say('bad', 'Photo access is off. Turn it on in Settings to change your picture.');
        return;
      }

      const result = await ImagePicker.launchImageLibraryAsync({
        mediaTypes: ['images'],
        allowsEditing: true,
        aspect: [1, 1],
        quality: 0.7,
        base64: true,
      });

      const asset = result.canceled ? null : result.assets[0];
      if (!asset?.base64) return;

      setUploadingAvatar(true);

      const url = await uploadAvatar(userId, {
        base64: asset.base64,
        mimeType: asset.mimeType ?? 'image/jpeg',
      });

      await updateProfile(userId, { avatar_url: url });
      await refreshProfile();
      say('good', 'Picture updated.');
    } catch (error) {
      fail(error);
    } finally {
      setUploadingAvatar(false);
    }
  };

  const handleUnblock = async (user: BlockedUser) => {
    setUnblocking(user.user_id);
    try {
      await unblockUser(userId, user.user_id);
      setBlocked((current) => (current ?? []).filter((row) => row.user_id !== user.user_id));
      say('good', `${user.display_name} is unblocked.`);
    } catch (error) {
      fail(error);
    } finally {
      setUnblocking(null);
    }
  };

  return (
    <SafeAreaView style={styles.safe} edges={['top']}>
      <Banner message={banner} onDismiss={() => setBanner(null)} />

      <ScrollView contentContainerStyle={styles.content} keyboardShouldPersistTaps="handled">
        <Text style={styles.title}>Profile</Text>

        <View style={styles.identity}>
          <Pressable
            accessibilityRole="button"
            accessibilityLabel="Change your picture"
            disabled={uploadingAvatar}
            onPress={() => void pickAvatar()}
            style={({ pressed }) => [pressed ? styles.pressed : null]}
          >
            {profile.avatar_url ? (
              <Image
                source={{ uri: profile.avatar_url }}
                style={styles.avatar}
                contentFit="cover"
              />
            ) : (
              <View style={[styles.avatar, styles.avatarFallback]}>
                <Text style={styles.avatarText}>
                  {profile.display_name.charAt(0).toUpperCase()}
                </Text>
              </View>
            )}
            <Text style={styles.avatarHint}>
              {uploadingAvatar ? 'Uploading…' : 'Change'}
            </Text>
          </Pressable>

          <View style={styles.identityText}>
            <Text style={styles.school}>{profile.school.name}</Text>
            <Text style={styles.domain}>@{profile.school.email_domain}</Text>
          </View>
        </View>

        <TextField
          label="Display name"
          value={name}
          onChangeText={setName}
          maxLength={40}
          autoCapitalize="words"
          editable={!saving}
        />

        <TextField
          label="Bio"
          value={bio}
          onChangeText={setBio}
          maxLength={BIO_MAX}
          multiline
          editable={!saving}
          placeholder="Optional"
          hint={`Anyone at ${profile.school.name} can read this — don't put your number or socials here. ${BIO_MAX - bio.length} left.`}
        />

        <View style={styles.pair}>
          <View style={styles.pairItem}>
            <TextField
              label="Pronouns"
              value={pronouns}
              onChangeText={setPronouns}
              maxLength={PRONOUNS_MAX}
              autoCapitalize="none"
              editable={!saving}
              placeholder="Optional"
            />
          </View>
          <View style={styles.pairItem}>
            <TextField
              label="Major"
              value={major}
              onChangeText={setMajor}
              maxLength={MAJOR_MAX}
              editable={!saving}
              placeholder="Optional"
            />
          </View>
        </View>

        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Year</Text>
          <View style={styles.chipRow}>
            {CLASS_YEARS.map((year) => {
              const on = classYear === year.value;
              return (
                <Pressable
                  key={year.value}
                  accessibilityRole="button"
                  accessibilityState={{ selected: on }}
                  disabled={saving}
                  // Tapping the current year clears it — everything here is optional.
                  onPress={() => setClassYear(on ? null : year.value)}
                  style={({ pressed }) => [
                    styles.chip,
                    on ? styles.chipOn : null,
                    pressed ? styles.pressed : null,
                  ]}
                >
                  <Text style={[styles.chipText, on ? styles.chipTextOn : null]}>
                    {year.label}
                  </Text>
                </Pressable>
              );
            })}
          </View>
        </View>

        {dirty ? (
          <Button label="Save profile" onPress={() => void save()} loading={saving} />
        ) : null}

        <View style={styles.section}>
          <Text style={styles.sectionTitle}>
            Interests · {interests.length}/{MAX_INTERESTS}
          </Text>
          <Text style={styles.muted}>Saved as you tap.</Text>
          <InterestPicker
            selected={interests}
            onToggle={(slug) => void toggleInterest(slug)}
            max={MAX_INTERESTS}
          />
        </View>

        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Blocked</Text>

          {blocked === null ? (
            <Text style={styles.muted}>Loading…</Text>
          ) : blocked.length === 0 ? (
            <Text style={styles.muted}>
              Nobody. Blocking someone hides both of you from each other's feeds.
            </Text>
          ) : (
            blocked.map((user) => (
              <View key={user.user_id} style={styles.blockedRow}>
                <Text style={styles.blockedName} numberOfLines={1}>
                  {user.display_name}
                </Text>
                <Pressable
                  accessibilityRole="button"
                  disabled={unblocking === user.user_id}
                  onPress={() => void handleUnblock(user)}
                  style={({ pressed }) => [pressed ? styles.pressed : null]}
                >
                  <Text style={styles.unblock}>
                    {unblocking === user.user_id ? 'Unblocking…' : 'Unblock'}
                  </Text>
                </Pressable>
              </View>
            ))
          )}
        </View>

        <Button
          label="Sign out"
          variant="secondary"
          onPress={() => {
            setSigningOut(true);
            void signOut().finally(() => setSigningOut(false));
          }}
          loading={signingOut}
        />

        <Text style={styles.footnote}>
          This app stores no location data. A drop is a sentence and a timer.
        </Text>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: colors.bg },
  content: { padding: spacing.lg, gap: spacing.xl, paddingBottom: spacing.xxl },
  title: { color: colors.text, fontSize: 26, fontWeight: '800' },
  identity: { flexDirection: 'row', alignItems: 'center', gap: spacing.lg },
  avatar: { width: 56, height: 56, borderRadius: radius.pill },
  avatarFallback: {
    backgroundColor: colors.surfaceRaised,
    alignItems: 'center',
    justifyContent: 'center',
  },
  avatarText: { color: colors.text, fontSize: 22, fontWeight: '700' },
  avatarHint: {
    color: colors.textMuted,
    fontSize: 11,
    fontWeight: '600',
    textAlign: 'center',
    marginTop: spacing.xs,
  },
  identityText: { gap: 2, flexShrink: 1 },
  school: { color: colors.text, fontSize: 17, fontWeight: '700' },
  domain: { color: colors.textMuted, fontSize: 13 },
  pair: { flexDirection: 'row', gap: spacing.md },
  pairItem: { flex: 1 },
  section: { gap: spacing.md },
  sectionTitle: { color: colors.textMuted, fontSize: 13, fontWeight: '700' },
  muted: { color: colors.textMuted, fontSize: 13, lineHeight: 20 },
  chipRow: { flexDirection: 'row', flexWrap: 'wrap', gap: spacing.sm },
  chip: {
    backgroundColor: colors.surfaceRaised,
    borderRadius: radius.pill,
    borderWidth: 1,
    borderColor: colors.border,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm,
  },
  chipOn: { backgroundColor: colors.accent, borderColor: colors.accent },
  chipText: { color: colors.textMuted, fontSize: 13, fontWeight: '600' },
  chipTextOn: { color: colors.accentText },
  blockedRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    gap: spacing.md,
    backgroundColor: colors.surface,
    borderRadius: radius.md,
    borderWidth: 1,
    borderColor: colors.border,
    paddingHorizontal: spacing.lg,
    paddingVertical: spacing.md,
  },
  blockedName: { color: colors.text, fontSize: 15, fontWeight: '600', flexShrink: 1 },
  unblock: { color: colors.accent, fontSize: 14, fontWeight: '700' },
  pressed: { opacity: 0.6 },
  footnote: { color: colors.textMuted, fontSize: 12, lineHeight: 18 },
});
