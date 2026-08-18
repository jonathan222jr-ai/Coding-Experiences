import { useCallback, useEffect, useRef, useState } from 'react';

import {
  FEED_PAGE_SIZE,
  fetchFeed,
  fetchMyActiveDrops,
  type Drop,
  type FeedCursor,
  type FeedRow,
} from '../api/drops';

type FeedStatus = 'loading' | 'ready' | 'error';

export interface UseFeedResult {
  drops: FeedRow[];
  myDrops: Drop[];
  status: FeedStatus;
  error: string | null;
  refreshing: boolean;
  loadingMore: boolean;
  hasMore: boolean;
  refresh: () => Promise<void>;
  loadMore: () => Promise<void>;
  /** Drop a card out of the list without a round trip (used by optimistic responses). */
  removeDrop: (dropId: string) => void;
  /** Clear every drop by one author, after blocking them. */
  removeDropsByAuthor: (authorId: string) => void;
}

/**
 * @param group Category group slug to narrow the feed to, or null for all of
 *   it. Changing it refetches from the server rather than filtering what's
 *   already loaded — see fetchFeed().
 */
export function useFeed(userId: string, group: string | null = null): UseFeedResult {
  const [drops, setDrops] = useState<FeedRow[]>([]);
  const [myDrops, setMyDrops] = useState<Drop[]>([]);
  const [status, setStatus] = useState<FeedStatus>('loading');
  const [error, setError] = useState<string | null>(null);
  const [refreshing, setRefreshing] = useState(false);
  const [loadingMore, setLoadingMore] = useState(false);

  const cursor = useRef<FeedCursor | null>(null);
  const [hasMore, setHasMore] = useState(false);

  // Guards against a scroll-triggered loadMore landing after a refresh has
  // already reset the list, which would splice a stale page onto fresh data.
  const generation = useRef(0);
  const inFlight = useRef(false);

  const refresh = useCallback(async () => {
    const run = ++generation.current;
    inFlight.current = true;
    setRefreshing(true);
    setError(null);

    try {
      const [page, mine] = await Promise.all([
        fetchFeed(null, FEED_PAGE_SIZE, group),
        // Deliberately unfiltered: your own live drops are pinned above the
        // feed so the app doesn't appear to swallow them, and a filter you
        // picked to browse with shouldn't hide your own post.
        fetchMyActiveDrops(userId),
      ]);

      if (generation.current !== run) return;

      setDrops(page.drops);
      setMyDrops(mine);
      cursor.current = page.nextCursor;
      setHasMore(page.nextCursor !== null);
      setStatus('ready');
    } catch (e) {
      if (generation.current !== run) return;
      setError(e instanceof Error ? e.message : String(e));
      setStatus('error');
    } finally {
      if (generation.current === run) {
        setRefreshing(false);
        inFlight.current = false;
      }
    }
  }, [userId, group]);

  const loadMore = useCallback(async () => {
    if (inFlight.current || !cursor.current) return;

    const run = generation.current;
    inFlight.current = true;
    setLoadingMore(true);

    try {
      const page = await fetchFeed(cursor.current, FEED_PAGE_SIZE, group);

      if (generation.current !== run) return;

      setDrops((current) => {
        // The same drop can arrive twice if rows shifted between pages.
        const seen = new Set(current.map((drop) => drop.id));
        return [...current, ...page.drops.filter((drop) => !seen.has(drop.id))];
      });

      cursor.current = page.nextCursor;
      setHasMore(page.nextCursor !== null);
    } catch (e) {
      if (generation.current !== run) return;
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      if (generation.current === run) {
        setLoadingMore(false);
      }
      inFlight.current = false;
    }
  }, [group]);

  const removeDrop = useCallback((dropId: string) => {
    setDrops((current) => current.filter((drop) => drop.id !== dropId));
  }, []);

  // get_feed() already hides blocked users, but the page on screen was fetched
  // before the block existed. Sweep it locally rather than making the user
  // refresh to stop seeing someone they just blocked.
  const removeDropsByAuthor = useCallback((authorId: string) => {
    setDrops((current) => current.filter((drop) => drop.author_id !== authorId));
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  return {
    drops,
    myDrops,
    status,
    error,
    refreshing,
    loadingMore,
    hasMore,
    refresh,
    loadMore,
    removeDrop,
    removeDropsByAuthor,
  };
}
