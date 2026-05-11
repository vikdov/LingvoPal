import type { EvaluationMode } from '../types/practice.types';

const SHORT_WORD_MAX_LEN = 4;

// Normalization pipeline — must mirror backend answer_evaluator.py normalise() exactly:
// 1. lowercase
// 2. trim leading/trailing whitespace
// 3. collapse internal whitespace to single space
// 4. strip punctuation (retain letters, digits, apostrophes)
// 5. NFD decompose → remove diacritic combining marks
function normalize(s: string): string {
  let t = s.trim().toLowerCase();
  t = t.replace(/\s+/g, ' ');
  t = t.replace(/[^\w\s']/g, '').replace(/_/g, '');
  t = t.normalize('NFD').replace(/[̀-ͯ]/g, '');
  return t.trim();
}

function levenshtein(a: string, b: string): number {
  const m = a.length;
  const n = b.length;
  const dp: number[][] = Array.from({ length: m + 1 }, (_, i) =>
    Array.from({ length: n + 1 }, (_, j) => (i === 0 ? j : j === 0 ? i : 0)),
  );
  for (let i = 1; i <= m; i++) {
    for (let j = 1; j <= n; j++) {
      dp[i][j] =
        a[i - 1] === b[j - 1]
          ? dp[i - 1][j - 1]
          : 1 + Math.min(dp[i - 1][j], dp[i][j - 1], dp[i - 1][j - 1]);
    }
  }
  return dp[m][n];
}

const THRESHOLDS: Record<EvaluationMode, number> = {
  strict:    0.95,
  normal:    0.90,
  forgiving: 0.80,
};

export function evaluateAnswer(
  userAnswer: string,
  correctAnswer: string,
  mode: EvaluationMode,
): { isCorrect: boolean; similarity: number } {
  const u = normalize(userAnswer);
  const c = normalize(correctAnswer);

  if (u === c) return { isCorrect: true, similarity: 1 };

  // Short words require exact match — fuzzy threshold too permissive at ≤4 chars.
  if (c.length <= SHORT_WORD_MAX_LEN) {
    const maxLen = Math.max(u.length, c.length);
    const similarity = maxLen === 0 ? 1 : 1 - levenshtein(u, c) / maxLen;
    return { isCorrect: false, similarity };
  }

  if (mode === 'strict') {
    const maxLen = Math.max(u.length, c.length);
    const similarity = maxLen === 0 ? 1 : 1 - levenshtein(u, c) / maxLen;
    return { isCorrect: similarity >= THRESHOLDS.strict, similarity };
  }

  const maxLen = Math.max(u.length, c.length);
  const similarity = maxLen === 0 ? 1 : 1 - levenshtein(u, c) / maxLen;
  return { isCorrect: similarity >= THRESHOLDS[mode], similarity };
}
