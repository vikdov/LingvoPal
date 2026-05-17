interface PosColor {
  text: string;
  bg: string;
  border: string;
  hex: string;
}

const POS_MAP: Record<string, PosColor> = {
  noun:        { text: 'text-[#2195f3]', bg: 'bg-[#2195f3]/10', border: 'border-[#2195f3]', hex: '#2195f3' },
  verb:        { text: 'text-[#009687]', bg: 'bg-[#009687]/10', border: 'border-[#009687]', hex: '#009687' },
  adjective:   { text: 'text-[#9c27b0]', bg: 'bg-[#9c27b0]/10', border: 'border-[#9c27b0]', hex: '#9c27b0' },
  adverb:      { text: 'text-[#3f51b5]', bg: 'bg-[#3f51b5]/10', border: 'border-[#3f51b5]', hex: '#3f51b5' },
  'modal verb':{ text: 'text-[#009687]', bg: 'bg-[#009687]/10', border: 'border-[#009687]', hex: '#009687' },
  pronoun:     { text: 'text-[#795554]', bg: 'bg-[#795554]/10', border: 'border-[#795554]', hex: '#795554' },
  preposition: { text: 'text-[#795553]', bg: 'bg-[#795553]/10', border: 'border-[#795553]', hex: '#795553' },
  conjunction: { text: 'text-[#7cb83a]', bg: 'bg-[#7cb83a]/10', border: 'border-[#7cb83a]', hex: '#7cb83a' },
  article:     { text: 'text-[#f9936a]', bg: 'bg-[#f9936a]/10', border: 'border-[#f9936a]', hex: '#f9936a' },
  interjection:{ text: 'text-[#795553]', bg: 'bg-[#795553]/10', border: 'border-[#795553]', hex: '#795553' },
};

const DEFAULT_POS_COLOR: PosColor = {
  text: 'text-muted-foreground',
  bg: 'bg-muted',
  border: 'border-foreground',
  hex: '#888888',
};

export function getPosColor(pos: string | null): PosColor {
  if (!pos) return DEFAULT_POS_COLOR;
  return POS_MAP[pos.toLowerCase()] ?? DEFAULT_POS_COLOR;
}
