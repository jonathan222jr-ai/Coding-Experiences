import { useNavigation, useRoute, type RouteProp } from '@react-navigation/native';
import { Image } from 'expo-image';
import { useEffect, useState } from 'react';
import { Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import {
  classYearLabel,
  fetchPublicProfile,
  type PublicProfile,
} from '../api/profiles';
import { Button } from '../components/Button';
import { InterestChips } from '../components/InterestChips';
import { LoadingScreen } from '../components/LoadingScreen';
import { SafetyActions, type SafetyTarget } from '../components/SafetyActions';
import { Sheet } from '../components/Sheet';
import { useCurrentUser } from '../hooks/useAuth';
import type { AppStackParamList } from '../navigation/types';
import { colors, radius, spacing } from '../theme';

type PersonRoute = RouteProp<AppStackParamList, 'Person'>;

export function PersonScreen() {
  const navigation = useNavigation();
  const { userId: viewerId } = useCurrentUser();
  const { userId } = useRoute<PersonRoute>().params;

  const [person, setPerson] = useState<PublicProfile | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [safetyOpen, setSafetyOpen] = useState(false);

  useEffect(() => {
    let active = true;

    fetchPublicProfile(userId)
      .then((next) => {
        if (!active) return;
        if (!next) {
          // RLS hides other campuses, so "not found" and "not yours to see"
          // are the same answer on purpose.
          setError('That profile is not available.');
          return;
        }
        setPerson(next);
      })
      .catch((e: unknown) => {
        if (active) setError(e instanceof Error ? e.message : String(e));
      });

    return () => {
      active = false;
    };
  }, [userId]);

  if (error) {
    return (
      <SafeAreaView style={styles.safe}>
        <View style={styles.centered}>
          <Text style={styles.errorTitle}>Can't show this profile</Text>
          <Text style={styles.errorBody}>{error}</Text>
          <Button label="Go back" variant="secondary" onPress={() => navigation.goBack()} />
        </View>
      </SafeAreaView>
    );
  }

  if (!person) return <LoadingScreen />;

  const isMe = person.id === viewerId;
  const year = classYearLabel(person.class_year);
  const facts = [year, person.major].filter(Boolean).join(' · ');

  const safetyTarget: SafetyTarget = {
    type: 'user',
    targetId: person.id,
    subjectId: person.id,
    subjectName: person.display_name,
  };

  return (
    <SafeAreaView style={styles.safe} edges={['top']}>
      <View style={styles.header}>
        <Pressable onPress={() => navigation.goBack()} accessibilityRole="button">
          <Text style={styles.back}>‹ Back</Text>
        </Pressable>

        {!isMe ? (
          <Pressable
            accessibilityRole="button"
            accessibilityLabel={`Report or block ${person.display_name}`}
            hitSlop={10}
            onPress={() => setSafetyOpen(true)}
          >
            <Text style={styles.more}>⋯</Text>
          </Pressable>
        ) : null}
      </View>

      <ScrollView contentContainerStyle={styles.content}>
        {person.avatar_url ? (
          <Image source={{ uri: person.avatar_url }} style={styles.avatar} contentFit="cover" />
        ) : (
          <View style={[styles.avatar, styles.avatarFallback]}>
            <Text style={styles.avatarText}>
              {person.display_name.charAt(0).toUpperCase()}
            </Text>
          </View>
        )}

        <View style={styles.nameBlock}>
          <Text style={styles.name}>{person.display_name}</Text>
          {person.pronouns ? <Text style={styles.pronouns}>{person.pronouns}</Text> : null}
          {facts ? <Text style={styles.facts}>{facts}</Text> : null}
        </View>

        {person.bio ? <Text style={styles.bio}>{person.bio}</Text> : null}

        {person.interests.length > 0 ? (
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>Into</Text>
            <InterestChips slugs={person.interests} />
          </View>
        ) : null}

        {!person.bio && person.interests.length === 0 && !facts ? (
          <Text style={styles.empty}>
            {person.display_name} hasn't filled anything in yet.
          </Text>
        ) : null}
      </ScrollView>

      <Sheet
        visible={safetyOpen}
        title={person.display_name}
        onClose={() => setSafetyOpen(false)}
      >
        <SafetyActions
          target={safetyTarget}
          currentUserId={viewerId}
          onClose={() => setSafetyOpen(false)}
          onBlocked={() => navigation.goBack()}
          onReported={() => setSafetyOpen(false)}
          onError={(message) => setError(message)}
        />
      </Sheet>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: colors.bg },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: spacing.lg,
    paddingVertical: spacing.md,
  },
  back: { color: colors.textMuted, fontSize: 16 },
  more: { color: colors.textMuted, fontSize: 22, fontWeight: '800' },
  content: { padding: spacing.xl, alignItems: 'center', gap: spacing.lg },
  avatar: { width: 96, height: 96, borderRadius: radius.pill },
  avatarFallback: {
    backgroundColor: colors.surfaceRaised,
    alignItems: 'center',
    justifyContent: 'center',
  },
  avatarText: { color: colors.text, fontSize: 36, fontWeight: '700' },
  nameBlock: { alignItems: 'center', gap: spacing.xs },
  name: { color: colors.text, fontSize: 24, fontWeight: '800' },
  pronouns: { color: colors.textMuted, fontSize: 14 },
  facts: { color: colors.textMuted, fontSize: 15 },
  bio: {
    color: colors.text,
    fontSize: 16,
    lineHeight: 24,
    textAlign: 'center',
  },
  section: { alignSelf: 'stretch', gap: spacing.md, alignItems: 'center' },
  sectionTitle: { color: colors.textMuted, fontSize: 13, fontWeight: '700' },
  empty: { color: colors.textMuted, fontSize: 14, textAlign: 'center' },
  centered: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    gap: spacing.md,
    padding: spacing.xl,
  },
  errorTitle: { color: colors.text, fontSize: 20, fontWeight: '700' },
  errorBody: { color: colors.textMuted, fontSize: 15, textAlign: 'center' },
});
