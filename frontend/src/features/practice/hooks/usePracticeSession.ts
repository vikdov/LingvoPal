import { usePracticeStore } from '../store/practice.store';

// Derived state on top of the raw store — components use this, not the store directly.
export function usePracticeSession() {
  const store = usePracticeStore();
  const currentItem = store.items[store.currentIndex] ?? null;
  const isLastItem = store.currentIndex >= store.items.length - 1;
  const currentAnswer = currentItem ? (store.answers[currentItem.item_id] ?? null) : null;

  return {
    ...store,
    currentItem,
    isLastItem,
    currentAnswer,
    total: store.items.length,
  };
}
