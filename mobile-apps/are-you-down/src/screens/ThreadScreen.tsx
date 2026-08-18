import { useNavigation, useRoute, type RouteProp } from '@react-navigation/native';
import type { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { useCallback, useEffect, useMemo, useState } from 'react';
import {
  ActivityIndicator,
  FlatList,
  KeyboardAvoidingView,
  Platform,
  Pressable,
  StyleSheet,
  Text,
  TextInput,
  View,
} from 'react-native';
import { SafeAreaView, useSafeAreaInsets } from 'react-native-safe-area-context';

import { closeDrop } from '../api/drops';
import type { Gif } from '../api/gifs';
import type { Message } from '../api/messages';
import { MESSAGE_MAX } from '../api/messages';
import { fetchThreadDetail, type ThreadDetail } from '../api/threads';
import { Banner, type BannerMessage } from '../components/Banner';
import { Button } from '../components/Button';
import { CategoryChip } from '../components/CategoryChip';
import { GifImage } from '../components/GifImage';
import { GifPicker } from '../components/GifPicker';
import { LoadingScreen } from '../components/LoadingScreen';
import { MessageBubble } from '../components/MessageBubble';
import { SafetyActions, type SafetyTarget } from '../components/SafetyActions';
import { Sheet } from '../components/Sheet';
import { useCurrentUser } from '../hooks/useAuth';
import { useThreadChat } from '../hooks/useThreadChat';
import type { AppStackParamList } from '../navigation/types';
import { colors, radius, spacing } from '../theme';

type ThreadRoute = RouteProp<AppStackParamList, 'Thread'>;
type Navigation = NativeStackNavigationProp<AppStackParamList>;

type SheetState =
  | null
  | { mode: 'members' }
  | { mode: 'gifs' }
  | { mode: 'safety'; target: SafetyTarget };

export function ThreadScreen() {
  const navigation = useNavigation<Navigation>();
  const { threadId } = useRoute<ThreadRoute>().params;
  const { userId } = useCurrentUser();
  const insets = useSafeAreaInsets();

  const [detail, setDetail] = useState<ThreadDetail | null>(null);
  const [detailError, setDetailError] = useState<string | null>(null);
  const [draft, setDraft] = useState('');
  const [sending, setSending] = useState(false);
  const [closing, setClosing] = useState(false);
  const [banner, setBanner] = useState<BannerMessage | null>(null);

  // One Modal, two modes. Stacking Modals is unreliable on iOS, so picking a
  // member swaps the content in place rather than presenting a second sheet.
  const [sheet, setSheet] = useState<SheetState>(null);

  const chat = useThreadChat(threadId, userId);

  useEffect(() => {
    let active = true;

    fetchThreadDetail(threadId)
      .then((next) => {
        if (active) setDetail(next);
      })
      .catch((error: unknown) => {
        if (active) {
          setDetailError(error instanceof Error ? error.message : String(error));
        }
      });

    return () => {
      active = false;
    };
  }, [threadId]);

  // Realtime hands us bare rows with a user_id and nothing else. A thread caps
  // at six people, so resolve names from the member list instead of joining
  // profiles on every message.
  const nameById = useMemo(() => {
    const map = new Map<string, string>();
    detail?.members.forEach((member) => map.set(member.user_id, member.display_name));
    return map;
  }, [detail]);

  const isAuthor = detail?.drop.user_id === userId;
  const canClose = isAuthor && detail?.drop.status === 'open';

  const handleClose = async () => {
    if (!detail) return;

    setClosing(true);
    try {
      const updated = await closeDrop(detail.drop.id);
      setDetail({ ...detail, drop: { ...detail.drop, status: updated.status } });
      setBanner({ key: Date.now(), tone: 'good', text: 'Closed. Nobody else can join.' });
    } catch (error) {
      setBanner({
        key: Date.now(),
        tone: 'bad',
        text: error instanceof Error ? error.message : String(error),
      });
    } finally {
      setClosing(false);
    }
  };

  const handleSend = async (gif?: Gif) => {
    const body = draft.trim();
    if ((body.length === 0 && !gif) || sending) return;

    setSending(true);
    // Clear immediately so typing never fights the round trip; restored below
    // if the send fails.
    setDraft('');

    try {
      await chat.send(body, gif);
    } catch (error) {
      setDraft(body);
      setBanner({
        key: Date.now(),
        tone: 'bad',
        text: error instanceof Error ? error.message : String(error),
      });
    } finally {
      setSending(false);
    }
  };

  const reportMessage = useCallback(
    (message: Message) =>
      setSheet({
        mode: 'safety',
        target: {
          type: 'message',
          targetId: message.id,
          subjectId: message.user_id,
          subjectName: nameById.get(message.user_id) ?? 'Someone',
          // A GIF-only message has no text to excerpt.
          preview: message.body ?? 'GIF',
        },
      }),
    [nameById],
  );

  const renderItem = useCallback(
    ({ item, index }: { item: Message; index: number }) => {
      // Inverted list: the bubble rendered above this one is the next index.
      const previous = chat.messages[index + 1];

      return (
        <MessageBubble
          body={item.body}
          gifUrl={item.gif_url}
          gifWidth={item.gif_width}
          gifHeight={item.gif_height}
          gifAlt={item.gif_alt}
          createdAt={item.created_at}
          authorName={nameById.get(item.user_id) ?? 'Someone'}
          mine={item.user_id === userId}
          showAuthor={previous?.user_id !== item.user_id}
          onLongPress={() => reportMessage(item)}
        />
      );
    },
    [chat.messages, nameById, userId, reportMessage],
  );

  if (detailError) {
    return (
      <SafeAreaView style={styles.safe}>
        <View style={styles.centered}>
          <Text style={styles.errorTitle}>Can't open this thread</Text>
          <Text style={styles.errorBody}>{detailError}</Text>
          <Button label="Go back" variant="secondary" onPress={() => navigation.goBack()} />
        </View>
      </SafeAreaView>
    );
  }

  if (!detail) {
    return <LoadingScreen />;
  }

  const statusNote =
    detail.drop.status === 'open'
      ? null
      : detail.drop.status === 'closed'
        ? 'This drop is closed — nobody new can join.'
        : 'This drop expired — nobody new can join.';

  return (
    <SafeAreaView style={styles.safe} edges={['top']}>
      <View style={styles.header}>
        <View style={styles.headerTop}>
          <Pressable onPress={() => navigation.goBack()} accessibilityRole="button">
            <Text style={styles.back}>‹ Back</Text>
          </Pressable>

          <Pressable
            accessibilityRole="button"
            accessibilityLabel="See who's here, report or block"
            hitSlop={8}
            onPress={() => setSheet({ mode: 'members' })}
          >
            <Text style={styles.members}>
              {detail.members.length} {detail.members.length === 1 ? 'person' : 'people'} ⌄
            </Text>
          </Pressable>
        </View>

        <CategoryChip category={detail.drop.category} />

        <Text style={styles.dropBody}>{detail.drop.body}</Text>

        {/* Small on purpose: the header is context for the conversation, not
            the post itself. */}
        {detail.drop.gif_url ? (
          <GifImage
            url={detail.drop.gif_url}
            width={detail.drop.gif_width}
            height={detail.drop.gif_height}
            alt={detail.drop.gif_alt}
            maxWidth={140}
          />
        ) : null}

        <Text style={styles.safety}>
          Meet in a public place. Tell someone where you're going.
        </Text>

        {statusNote ? <Text style={styles.statusNote}>{statusNote}</Text> : null}

        {canClose ? (
          <Button
            label="Close drop"
            variant="secondary"
            onPress={() => void handleClose()}
            loading={closing}
            style={styles.closeButton}
          />
        ) : null}
      </View>

      {chat.connection === 'error' ? (
        <Text style={styles.connection}>Reconnecting…</Text>
      ) : null}

      <Banner message={banner} onDismiss={() => setBanner(null)} />

      <KeyboardAvoidingView
        style={styles.flex}
        behavior={Platform.OS === 'ios' ? 'padding' : undefined}
        keyboardVerticalOffset={Platform.OS === 'ios' ? 8 : 0}
      >
        {chat.status === 'loading' ? (
          <ActivityIndicator color={colors.accent} style={styles.spinner} />
        ) : chat.status === 'error' ? (
          <View style={styles.centered}>
            <Text style={styles.errorBody}>{chat.error}</Text>
            <Button label="Try again" variant="secondary" onPress={() => void chat.retry()} />
          </View>
        ) : (
          <FlatList
            inverted
            data={chat.messages}
            keyExtractor={(item) => item.id}
            renderItem={renderItem}
            contentContainerStyle={styles.list}
            keyboardDismissMode="interactive"
            onEndReachedThreshold={0.3}
            onEndReached={() => void chat.loadOlder()}
            ListFooterComponent={
              chat.loadingOlder ? (
                <ActivityIndicator color={colors.textMuted} style={styles.spinner} />
              ) : null
            }
            ListEmptyComponent={
              <View style={styles.emptyChat}>
                <Text style={styles.emptyChatText}>
                  You're in. Someone has to say something first.
                </Text>
              </View>
            }
          />
        )}

        {/* SafeAreaView only claims the top edge here, so the composer has to
            clear the home indicator itself. */}
        <View style={[styles.composer, { paddingBottom: Math.max(insets.bottom, spacing.md) }]}>
          <TextInput
            value={draft}
            onChangeText={setDraft}
            placeholder="Message"
            placeholderTextColor={colors.textMuted}
            style={styles.input}
            multiline
            maxLength={MESSAGE_MAX}
            editable={!sending}
          />
          <Pressable
            accessibilityRole="button"
            accessibilityLabel="Add a GIF"
            onPress={() => setSheet({ mode: 'gifs' })}
            disabled={sending}
            style={({ pressed }) => [styles.gifButton, pressed ? styles.sendPressed : null]}
          >
            <Text style={styles.gifButtonText}>GIF</Text>
          </Pressable>

          <Pressable
            accessibilityRole="button"
            accessibilityLabel="Send"
            onPress={() => void handleSend()}
            disabled={draft.trim().length === 0 || sending}
            style={({ pressed }) => [
              styles.send,
              draft.trim().length === 0 || sending ? styles.sendOff : null,
              pressed ? styles.sendPressed : null,
            ]}
          >
            <Text style={styles.sendIcon}>↑</Text>
          </Pressable>
        </View>
      </KeyboardAvoidingView>

      <Sheet
        visible={sheet !== null}
        title={
          sheet?.mode === 'safety'
            ? sheet.target.subjectName
            : sheet?.mode === 'gifs'
              ? 'Send a GIF'
              : 'Who’s here'
        }
        subtitle={
          sheet?.mode === 'safety'
            ? sheet.target.preview
            : sheet?.mode === 'gifs'
              ? undefined
              : 'Meet in a public place. You can report or block anyone here.'
        }
        onClose={() => setSheet(null)}
      >
        {sheet?.mode === 'gifs' ? (
          <GifPicker
            onPick={(gif) => {
              setSheet(null);
              void handleSend(gif);
            }}
          />
        ) : sheet?.mode === 'safety' ? (
          <SafetyActions
            target={sheet.target}
            currentUserId={userId}
            onClose={() => setSheet(null)}
            onBlocked={(_id, name) =>
              setBanner({
                key: Date.now(),
                tone: 'good',
                text: `${name} is blocked. You won't see each other's drops.`,
              })
            }
            onReported={() =>
              setBanner({ key: Date.now(), tone: 'good', text: "Thanks — we'll take a look." })
            }
            onError={(message) => setBanner({ key: Date.now(), tone: 'bad', text: message })}
            onViewProfile={(id) => {
              setSheet(null);
              navigation.navigate('Person', { userId: id });
            }}
          />
        ) : sheet?.mode === 'members' ? (
          <View style={styles.memberList}>
            {detail.members.map((member) => {
              const isMe = member.user_id === userId;

              return (
                <Pressable
                  key={member.user_id}
                  accessibilityRole="button"
                  disabled={isMe}
                  onPress={() =>
                    setSheet({
                      mode: 'safety',
                      target: {
                        type: 'user',
                        targetId: member.user_id,
                        subjectId: member.user_id,
                        subjectName: member.display_name,
                      },
                    })
                  }
                  style={({ pressed }) => [
                    styles.memberRow,
                    pressed && !isMe ? styles.memberRowPressed : null,
                  ]}
                >
                  <Text style={styles.memberName}>
                    {member.display_name}
                    {member.user_id === detail.drop.user_id ? ' · posted this' : ''}
                  </Text>
                  <Text style={styles.memberAction}>{isMe ? 'You' : 'Report or block'}</Text>
                </Pressable>
              );
            })}

            <Button label="Done" variant="ghost" onPress={() => setSheet(null)} />
          </View>
        ) : null}
      </Sheet>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: colors.bg },
  flex: { flex: 1 },
  header: {
    paddingHorizontal: spacing.lg,
    paddingBottom: spacing.md,
    gap: spacing.sm,
    borderBottomWidth: 1,
    borderBottomColor: colors.border,
  },
  headerTop: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingVertical: spacing.sm,
  },
  back: { color: colors.textMuted, fontSize: 16 },
  members: { color: colors.textMuted, fontSize: 13, fontWeight: '600' },
  dropBody: { color: colors.text, fontSize: 17, fontWeight: '700', lineHeight: 24 },
  safety: { color: colors.textMuted, fontSize: 12, lineHeight: 17 },
  statusNote: { color: colors.accent, fontSize: 12, fontWeight: '600' },
  closeButton: { marginTop: spacing.xs },
  connection: {
    color: colors.textMuted,
    fontSize: 12,
    textAlign: 'center',
    paddingVertical: spacing.sm,
  },
  list: { padding: spacing.lg, flexGrow: 1, justifyContent: 'flex-end' },
  spinner: { marginVertical: spacing.lg },
  emptyChat: {
    // The list is inverted, so its empty state has to be flipped back upright.
    transform: [{ scaleY: -1 }],
    alignItems: 'center',
    paddingVertical: spacing.xxl,
  },
  emptyChatText: {
    color: colors.textMuted,
    fontSize: 14,
    textAlign: 'center',
    paddingHorizontal: spacing.xl,
  },
  composer: {
    flexDirection: 'row',
    alignItems: 'flex-end',
    gap: spacing.sm,
    padding: spacing.md,
    borderTopWidth: 1,
    borderTopColor: colors.border,
  },
  input: {
    flex: 1,
    backgroundColor: colors.surface,
    borderRadius: radius.lg,
    borderWidth: 1,
    borderColor: colors.border,
    color: colors.text,
    fontSize: 16,
    paddingHorizontal: spacing.lg,
    paddingTop: spacing.md,
    paddingBottom: spacing.md,
    maxHeight: 120,
  },
  send: {
    width: 44,
    height: 44,
    borderRadius: radius.pill,
    backgroundColor: colors.accent,
    alignItems: 'center',
    justifyContent: 'center',
  },
  // Filled rather than outlined: as a muted outline next to a muted-outline
  // text field it read as decoration, and nobody found the GIF picker.
  gifButton: {
    height: 44,
    paddingHorizontal: spacing.md,
    borderRadius: radius.pill,
    backgroundColor: colors.surfaceRaised,
    borderWidth: 1,
    borderColor: colors.border,
    alignItems: 'center',
    justifyContent: 'center',
  },
  gifButtonText: { color: colors.text, fontSize: 13, fontWeight: '800', letterSpacing: 0.5 },
  sendOff: { opacity: 0.4 },
  sendPressed: { opacity: 0.75 },
  sendIcon: { color: colors.accentText, fontSize: 20, fontWeight: '800' },
  centered: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    gap: spacing.md,
    padding: spacing.xl,
  },
  memberList: { gap: spacing.sm },
  memberRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    gap: spacing.md,
    backgroundColor: colors.surfaceRaised,
    borderRadius: radius.md,
    paddingHorizontal: spacing.lg,
    paddingVertical: spacing.lg - 4,
  },
  memberRowPressed: { opacity: 0.7 },
  memberName: { color: colors.text, fontSize: 15, fontWeight: '600', flexShrink: 1 },
  memberAction: { color: colors.textMuted, fontSize: 12 },
  errorTitle: { color: colors.text, fontSize: 20, fontWeight: '700' },
  errorBody: { color: colors.textMuted, fontSize: 15, textAlign: 'center', lineHeight: 22 },
});
