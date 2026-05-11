interface PosColor {
  text: string;
  bg: string;
}

const POS_MAP: Record<string, PosColor> = {
  noun:        { text: 'text-blue-600',   bg: 'bg-blue-50' },
  verb:        { text: 'text-emerald-600', bg: 'bg-emerald-50' },
  adjective:   { text: 'text-violet-600', bg: 'bg-violet-50' },
  adverb:      { text: 'text-orange-500', bg: 'bg-orange-50' },
  'modal verb':{ text: 'text-teal-600',   bg: 'bg-teal-50' },
  pronoun:     { text: 'text-cyan-600',   bg: 'bg-cyan-50' },
  preposition: { text: 'text-indigo-600', bg: 'bg-indigo-50' },
  conjunction: { text: 'text-pink-600',   bg: 'bg-pink-50' },
  article:     { text: 'text-rose-500',   bg: 'bg-rose-50' },
  interjection:{ text: 'text-yellow-600', bg: 'bg-yellow-50' },
};

const DEFAULT_POS_COLOR: PosColor = {
  text: 'text-muted-foreground',
  bg: 'bg-muted',
};

export function getPosColor(pos: string | null): PosColor {
  if (!pos) return DEFAULT_POS_COLOR;
  return POS_MAP[pos.toLowerCase()] ?? DEFAULT_POS_COLOR;
}
