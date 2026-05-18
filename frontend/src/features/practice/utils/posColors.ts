interface PosColor {
  text: string;
  bg: string;
  border: string;
  /** CSS variable reference — usable in inline `style={{ color }}` props */
  hex: string;
}

const POS_MAP: Record<string, PosColor> = {
  noun:         { text: 'text-pos-noun',         bg: 'bg-pos-noun/10',         border: 'border-pos-noun',         hex: 'var(--pos-noun)' },
  verb:         { text: 'text-pos-verb',         bg: 'bg-pos-verb/10',         border: 'border-pos-verb',         hex: 'var(--pos-verb)' },
  adjective:    { text: 'text-pos-adjective',    bg: 'bg-pos-adjective/10',    border: 'border-pos-adjective',    hex: 'var(--pos-adjective)' },
  adverb:       { text: 'text-pos-adverb',       bg: 'bg-pos-adverb/10',       border: 'border-pos-adverb',       hex: 'var(--pos-adverb)' },
  'modal verb': { text: 'text-pos-verb',         bg: 'bg-pos-verb/10',         border: 'border-pos-verb',         hex: 'var(--pos-verb)' },
  pronoun:      { text: 'text-pos-pronoun',      bg: 'bg-pos-pronoun/10',      border: 'border-pos-pronoun',      hex: 'var(--pos-pronoun)' },
  preposition:  { text: 'text-pos-preposition',  bg: 'bg-pos-preposition/10',  border: 'border-pos-preposition',  hex: 'var(--pos-preposition)' },
  conjunction:  { text: 'text-pos-conjunction',  bg: 'bg-pos-conjunction/10',  border: 'border-pos-conjunction',  hex: 'var(--pos-conjunction)' },
  article:      { text: 'text-pos-article',      bg: 'bg-pos-article/10',      border: 'border-pos-article',      hex: 'var(--pos-article)' },
  interjection: { text: 'text-pos-interjection', bg: 'bg-pos-interjection/10', border: 'border-pos-interjection', hex: 'var(--pos-interjection)' },
};

const DEFAULT_POS_COLOR: PosColor = {
  text: 'text-muted-foreground',
  bg: 'bg-muted',
  border: 'border-foreground',
  hex: 'var(--pos-default)',
};

export function getPosColor(pos: string | null): PosColor {
  if (!pos) return DEFAULT_POS_COLOR;
  return POS_MAP[pos.toLowerCase()] ?? DEFAULT_POS_COLOR;
}
