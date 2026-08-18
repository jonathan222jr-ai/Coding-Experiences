import { useCallback, useEffect, useRef, useState } from 'react';

import {
  fetchMessages,
  MESSAGE_PAGE_SIZE,
  sendMessage as sendMessageApi,
  subscribeToThread,
  type Message,
  type OutgoingGif,
  type ThreadChannelStatus,
} from '../api/messages';

type ChatStatus = 'loading' | 'ready' | 'error';

export interface UseThreadChatResult {
  /** Newest first, matching the inverted list. */
  messages: Message[];
  status: ChatStatus;
  error: string | null;
  connection: ThreadChannelStatus;
  hasOlder: boolean;
  loadingOlder: boolean;
  send: (body: string, gif?: OutgoingGif | null) => Promise<void>;
  loadOlder: () => Promise<void>;
  retry: () => Promise<void>;
}

function newestFirst(a: Message, b: Message): number {
  const delta = Date.parse(b.created_at) - Date.parse(a.created_at);
  // Two messages can land in the same millisecond; keep the order stable.
  return delta !== 0 ? delta : b.id.localeCompare(a.id);
}

export function useThreadChat(threadId: string, userId: string): UseThreadChatResult {
  const [messages, setMessages] = useState<Message[]>([]);
  const [status, setStatus] = useState<ChatStatus>('loading');
  const [error, setError] = useState<string | null>(null);
  const [connection, setConnection] = useState<ThreadChannelStatus>('joining');
  const [hasOlder, setHasOlder] = useState(false);
  const [loadingOlder, setLoadingOlder] = useState(false);

  const mounted = useRef(true);

  const merge = useCallback((incoming: Message[]) => {
    if (incoming.length === 0) return;

    setMessages((current) => {
      const byId = new Map(current.map((message) => [message.id, message]));
      let changed = false;

      for (const message of incoming) {
        if (!byId.has(message.id)) {
          byId.set(message.id, message);
          changed = true;
        }
      }

      // Our own sends arrive twice — once from the insert's returned row and
      // again over realtime. Bail out rather than churn the list.
      return changed ? [...byId.values()].sort(newestFirst) : current;
    });
  }, []);

  const loadLatest = useCallback(async () => {
    const page = await fetchMessages(threadId);
    if (!mounted.current) return;
    merge(page);
    setHasOlder(page.length === MESSAGE_PAGE_SIZE);
    setStatus('ready');
    setError(null);
  }, [threadId, merge]);

  useEffect(() => {
    mounted.current = true;

    void loadLatest().catch((e: unknown) => {
      if (!mounted.current) return;
      setError(e instanceof Error ? e.message : String(e));
      setStatus('error');
    });

    const unsubscribe = subscribeToThread(threadId, {
      onMessage: (message) => {
        if (mounted.current) merge([message]);
      },
      onStatusChange: (next) => {
        if (!mounted.current) return;
        setConnection(next);

        // Anything sent between the initial fetch and the channel going live —
        // or while it was dropped — never reached us. Refetch on every join.
        if (next === 'live') {
          void loadLatest().catch(() => {
            /* the existing transcript stays on screen */
          });
        }
      },
    });

    return () => {
      mounted.current = false;
      unsubscribe();
    };
  }, [threadId, merge, loadLatest]);

  const send = useCallback(
    async (body: string, gif?: OutgoingGif | null) => {
      const message = await sendMessageApi(threadId, userId, body, gif);
      merge([message]);
    },
    [threadId, userId, merge],
  );

  const loadOlder = useCallback(async () => {
    if (loadingOlder || !hasOlder) return;

    const oldest = messages[messages.length - 1];
    if (!oldest) return;

    setLoadingOlder(true);

    try {
      const page = await fetchMessages(threadId, oldest.created_at);
      if (!mounted.current) return;
      merge(page);
      setHasOlder(page.length === MESSAGE_PAGE_SIZE);
    } catch (e) {
      if (mounted.current) {
        setError(e instanceof Error ? e.message : String(e));
      }
    } finally {
      if (mounted.current) setLoadingOlder(false);
    }
  }, [threadId, messages, hasOlder, loadingOlder, merge]);

  const retry = useCallback(async () => {
    setStatus('loading');
    try {
      await loadLatest();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
      setStatus('error');
    }
  }, [loadLatest]);

  return {
    messages,
    status,
    error,
    connection,
    hasOlder,
    loadingOlder,
    send,
    loadOlder,
    retry,
  };
}
