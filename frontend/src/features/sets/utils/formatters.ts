import type { LanguageRef } from '@/features/languages';

export function langName(id: number | null | undefined, languages: LanguageRef[]): string {
  if (id == null) return '';
  return languages.find((l) => l.id === id)?.name ?? String(id);
}

export function difficultyLabel(difficulty: number | null): string {
  if (difficulty === null) return '';
  const labels = ['', 'A1', 'A2', 'B1', 'B2', 'C1', 'C2', 'Native'];
  return labels[difficulty] ?? String(difficulty);
}
