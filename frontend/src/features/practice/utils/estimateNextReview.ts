const HOUR = 60 * 60 * 1000;
const DAY = 24 * HOUR;

// Rough frontend estimate — actual SM-2 is calculated by backend at finalize.
export function estimateNextReview(
  lastReviewed: string | null,
  isCorrect: boolean,
): Date {
  if (!isCorrect) return new Date(Date.now() + DAY);
  // New item (never reviewed): 6-hour initial interval
  if (!lastReviewed) return new Date(Date.now() + 6 * HOUR);
  // Known item correct: ~1 day (conservative estimate)
  return new Date(Date.now() + DAY);
}
