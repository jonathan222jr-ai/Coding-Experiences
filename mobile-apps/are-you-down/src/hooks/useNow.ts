import { useSyncExternalStore } from 'react';

/**
 * One clock for the whole app.
 *
 * Every drop card shows a live countdown. Giving each card its own interval
 * means twenty timers waking the JS thread out of phase with each other, so
 * instead there is a single ticker and cards subscribe to it.
 */

const subscribers = new Set<() => void>();
let timer: ReturnType<typeof setInterval> | null = null;
let now = Date.now();

function subscribe(callback: () => void): () => void {
  subscribers.add(callback);

  if (!timer) {
    timer = setInterval(() => {
      now = Date.now();
      subscribers.forEach((notify) => notify());
    }, 1000);
  }

  return () => {
    subscribers.delete(callback);

    if (subscribers.size === 0 && timer) {
      clearInterval(timer);
      timer = null;
    }
  };
}

function getSnapshot(): number {
  return now;
}

export function useNow(): number {
  return useSyncExternalStore(subscribe, getSnapshot, getSnapshot);
}
